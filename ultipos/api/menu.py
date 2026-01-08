import frappe
from ultipos.api.utils import build_items

@frappe.whitelist(allow_guest=True)
def get_menu(outlet_code):
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code})

    menu = frappe.get_all(
        "Menu",
        filters={
            "outlet": outlet.name,
            "status": "Active"
        },
        order_by="priority asc",
        limit=1
    )[0]

    categories = frappe.get_all(
        "Menu Category",
        filters={"menu": menu.name},
        order_by="sort_order asc"
    )

    response = []

    for cat in categories:
        items = frappe.get_all(
            "Menu Item",
            filters={
                "category": cat.name,
                "status": "Active",
                "show_in_menu": 1
            }
        )

        response.append({
            "category_id": cat.name,
            "category_name": cat.category_name,
            "items": build_items(items)
        })

    return {
        "outlet_code": outlet_code,
        "menu_id": menu.name,
        "categories": response
    }
