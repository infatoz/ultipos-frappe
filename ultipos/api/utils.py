import frappe


# ----------------------------
# MENU HELPERS
# ----------------------------

def build_items(menu_items):
    """
    Build menu item response with modifiers
    """
    response = []

    for item in menu_items:
        item_doc = frappe.get_doc("Menu Item", item.name)

        modifiers = []
        for mg in item_doc.item_modifier_groups:
            options = frappe.get_all(
                "Modifier Option",
                filters={"modifier_group": mg.modifier_group},
                fields=["name", "option_name", "price"]
            )

            modifiers.append({
                "group": mg.modifier_group,
                "min": mg.min_qty,
                "max": mg.max_qty,
                "required": mg.required,
                "options": [
                    {
                        "id": o.name,
                        "name": o.option_name,
                        "price": o.price
                    } for o in options
                ]
            })

        response.append({
            "item_id": item_doc.name,
            "name": item_doc.item_name,
            "price": item_doc.price,
            "is_modifier_item": item_doc.is_modifier_item,
            "modifiers": modifiers
        })

    return response


# ----------------------------
# ORDER HELPERS
# ----------------------------

def build_order_items(items):
    """
    Convert frontend items into Order Item child rows
    """
    rows = []

    for i in items:
        rows.append({
            "item_name": i["name"],
            "menu_item": i["item_id"],
            "qty": i["qty"],
            "price": i["price"],
            "total": i["price"] * i["qty"]
        })

    return rows


# ----------------------------
# COUPON VALIDATION (SIMPLE)
# ----------------------------

def validate_coupon(coupon_code, outlet, cart_total):
    coupon = frappe.get_doc(
        "Coupon",
        {
            "coupon_code": coupon_code,
            "outlet": outlet,
            "status": "Active"
        }
    )

    if cart_total < coupon.min_order_amount:
        frappe.throw("Minimum order value not met")

    if coupon.discount_type == "Percentage":
        return cart_total * coupon.discount_value / 100

    return coupon.discount_value
