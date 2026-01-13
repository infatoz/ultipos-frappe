import frappe
from ultipos.api.utils import get_outlet, build_items


@frappe.whitelist(allow_guest=True)
def get_menu(outlet_code):
    outlet = get_outlet(outlet_code)

    menu = frappe.get_all(
        "Menu",
        filters={"outlet": outlet.name, "status": "Active", "is_active": 1},
        fields=["name", "priority"],
        order_by="priority asc, modified desc",
        limit=1
    )
    if not menu:
        frappe.throw("No active menu for this outlet")

    menu_id = menu[0]["name"]

    categories = frappe.get_all(
        "Menu Category",
        filters={"menu": menu_id, "show_in_menu": 1},
        fields=["name", "category_name", "sort_order"],
        order_by="sort_order asc, modified asc"
    )

    response = []
    for cat in categories:
        items = frappe.get_all(
            "Menu Item",
            filters={
                "category": cat["name"],
                "status": "Active",
                "show_in_menu": 1,
                "is_modifier_item": 0
            },
            fields=["name"]
        )

        response.append({
            "category_id": cat["name"],
            "category_name": cat["category_name"],
            "items": build_items(items)
        })

    return {
        "outlet_code": outlet_code,
        "menu_id": menu_id,
        "categories": response
    }
