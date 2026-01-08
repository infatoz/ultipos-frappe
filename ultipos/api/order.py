import frappe
from ultipos.api.utils import build_order_items


@frappe.whitelist(allow_guest=True)
def place(outlet_code, customer_id, items, payment):
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code})

    order = frappe.new_doc("Order")
    order.outlet = outlet.name
    order.restaurant = outlet.restaurant
    order.customer = customer_id
    order.items = build_order_items(items)
    order.payment_method = payment["method"]
    order.transaction_id = payment["transaction_id"]
    order.insert(ignore_permissions=True)

    return {
        "order_id": order.name,
        "tracking_url": f"/track/{order.name}"
    }
