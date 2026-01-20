# utils.py:
import json
import frappe
from frappe.utils import now_datetime, getdate


def _loads(value):
    """
    Frappe sometimes sends args as JSON string.
    Always normalize to dict/list.
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def success(data=None, message="OK"):
    return {"ok": True, "message": message, "data": data}


def get_outlet(outlet_code: str):
    outlet_name = frappe.db.get_value("Outlet", {"outlet_code": outlet_code}, "name")
    if not outlet_name:
        frappe.throw("Invalid outlet_code")
    outlet = frappe.get_doc("Outlet", outlet_name)
    if outlet.status != "Active":
        frappe.throw("Outlet inactive")
    if int(outlet.is_accepting_orders or 0) != 1:
        frappe.throw("Outlet is not accepting orders currently")
    return outlet


def get_online_store_settings(restaurant_name: str):
    """
    Online Store Settings DocType: autoname field:restaurant
    """
    settings_name = frappe.db.get_value("Online Store Settings", {"restaurant": restaurant_name}, "name")
    if not settings_name:
        return None
    return frappe.get_doc("Online Store Settings", settings_name)


def get_worldline_settings(restaurant_name: str):
    settings_name = frappe.db.get_value(
        "Worldline Settings",
        {"restaurant": restaurant_name},
        "name"
    )

    if not settings_name:
        frappe.throw("Worldline Settings not configured for this restaurant")

    doc = frappe.get_doc("Worldline Settings", settings_name)

    if int(doc.is_enabled or 0) != 1:
        frappe.throw("Worldline is disabled for this restaurant")

    # ✅ validate required keys
    if not getattr(doc, "merchant_id", None):
        frappe.throw("Worldline Settings missing merchant_id")
    if not getattr(doc, "api_key", None):
        frappe.throw("Worldline Settings missing api_key")

    return doc



def normalize_money(x):
    try:
        return float(x or 0)
    except Exception:
        return 0.0


def build_modifier_group_payload(mod_group_name: str, min_qty=None, max_qty=None, required=False):
    group = frappe.get_doc("Modifier Group", mod_group_name)

    group_min = int(getattr(group, "min_qty", 0) or 0)
    group_max = int(getattr(group, "max_qty", 0) or 0)

    final_min = group_min
    final_max = group_max

    # override only if provided and > 0
    if min_qty is not None:
        try:
            if int(min_qty) > 0:
                final_min = int(min_qty)
        except Exception:
            pass

    if max_qty is not None:
        try:
            if int(max_qty) > 0:
                final_max = int(max_qty)
        except Exception:
            pass

    final_required = bool(required or getattr(group, "required", 0))

    options = frappe.get_all(
        "Modifier Option",
        filters={"modifier_group": group.name},
        fields=["name", "option_name", "price_delta", "is_item", "linked_item", "external_id"],
        order_by="modified asc",
    )

    return {
        "group_id": group.name,
        "name": group.group_name,
        "required": final_required,
        "min": final_min,
        "max": final_max,
        "options": [
            {
                "option_id": o["name"],
                "name": o["option_name"],
                "price": normalize_money(o.get("price_delta")),
                "is_item": bool(o.get("is_item")),
                "linked_item": o.get("linked_item"),
                "external_id": o.get("external_id"),
            }
            for o in options
        ],
    }

def resolve_item_modifier_groups(item_doc):
    """
    In DocTypes:
    - Menu Category has category_modifier_groups table
    - Menu Item has item_modifier_groups table
    Item can inherit category config (inherit_category_config)
    Item can override (override_category / inherit flag)
    """
    groups = []

    # 1) category groups
    if int(item_doc.inherit_category_config or 0) == 1:
        cat = frappe.get_doc("Menu Category", item_doc.category)

        for row in (cat.category_modifier_groups or []):
            groups.append(
                build_modifier_group_payload(
                    row.modifier_group,
                    min_qty=getattr(row, "min_qty", None),
                    max_qty=getattr(row, "max_qty", None),

                    required=row.required,
                )
            )

    # 2) item groups
    for row in (item_doc.item_modifier_groups or []):
        groups.append(
            build_modifier_group_payload(
                row.modifier_group,
                min_qty=getattr(row, "min_qty", None),
                max_qty=getattr(row, "max_qty", None),

                required=False,
            )
        )

    return groups


def build_items(menu_items):
    """
    menu_items: list rows from frappe.get_all(Menu Item)
    Returns frontend-friendly items payload
    """
    response_items = []

    for row in menu_items:
        item = frappe.get_doc("Menu Item", row.name)

        response_items.append(
            {
                "item_id": item.name,
                "name": item.item_name,
                "price": normalize_money(item.price),
                "image": item.image or "/files/ultipos-logo.png",
                "external_item_id": item.external_item_id,
                "is_modifier_item": bool(item.is_modifier_item),
                "customizations": resolve_item_modifier_groups(item),
            }
        )

    return response_items


def build_order_items(items):
    """
    Accepts items list:
    [
      {item_id/menu_item, qty, price?, notes?, modifiers:[{name, qty, price}]}
    ]
    Creates Order Item + Order Item Modifier rows (child tables)
    """
    items = _loads(items) or []
    if not isinstance(items, list) or not items:
        frappe.throw("Items list is required")

    rows = []
    for i in items:
        if not isinstance(i, dict):
            frappe.throw("Invalid item payload")

        menu_item_id = i.get("item_id") or i.get("menu_item")
        if not menu_item_id:
            frappe.throw("item_id is required")

        qty = int(i.get("qty") or 0)
        if qty <= 0:
            frappe.throw("qty must be > 0")

        # ✅ Fetch required fields without permission checks
        menu_item = frappe.db.get_value(
            "Menu Item",
            menu_item_id,
            ["name", "item_name", "price", "show_in_kds"],
            as_dict=True
        )

        if not menu_item:
            frappe.throw(f"Invalid menu item: {menu_item_id}")
            
        unit_price = normalize_money(i.get("price")) or normalize_money(menu_item.get("price"))

        total_price = unit_price * qty

        # modifiers (optional)
        modifiers = _loads(i.get("modifiers")) or []

        modifier_rows = []
        for m in modifiers:
            modifier_rows.append(
                {
                    "doctype": "Order Item Modifier",
                    "modifier_name": m.get("name") or m.get("modifier_name"),
                    "qty": int(m.get("qty") or 1),
                    "price": normalize_money(m.get("price") or 0),
                    "show_in_kds": 1,
                }
            )
            total_price += normalize_money(m.get("price") or 0) * int(m.get("qty") or 1)

        rows.append(
            {
                "doctype": "Order Item",
                "menu_item": menu_item.get("name"),
                "item_name": menu_item.get("item_name"),
                "show_in_kds": int(menu_item.get("show_in_kds") or 0),

                "qty": qty,
                "unit_price": unit_price,
                "total_price": total_price,
               
                "notes": i.get("notes"),
                "order_item_modifiers": modifier_rows,
            }
        )

    return rows