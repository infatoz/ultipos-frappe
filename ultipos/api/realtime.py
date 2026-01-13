import frappe


@frappe.whitelist(allow_guest=True)
def subscribe_order(order_id):
    if not frappe.db.exists("Order", order_id):
        frappe.throw("Invalid order")
    return {"status": "subscribed"}


def publish_order_status(order_id, status):
    frappe.publish_realtime(
        event=f"ultipos_order_status_{order_id}",
        message={"order_id": order_id, "status": status},
        after_commit=True
    )


def publish_new_order(outlet):
    frappe.publish_realtime(
        event="ultipos_new_order",
        message={"outlet": outlet},
        after_commit=True
    )
