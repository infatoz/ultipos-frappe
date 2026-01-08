import frappe


@frappe.whitelist(allow_guest=True)
def subscribe_order(order_id):
    """
    Called by frontend to confirm order exists.
    Actual realtime happens via frappe.realtime.
    """
    if not frappe.db.exists("Order", order_id):
        frappe.throw("Invalid order")

    return {"status": "subscribed"}


def publish_order_status(order_id, status):
    """
    Called internally when order status changes
    """
    frappe.publish_realtime(
        event=f"ultipos_order_status_{order_id}",
        message={
            "order_id": order_id,
            "status": status
        },
        after_commit=True
    )


def publish_new_order(outlet):
    """
    Notify outlet dashboard / POS about new order
    """
    frappe.publish_realtime(
        event="ultipos_new_order",
        message={
            "outlet": outlet
        },
        after_commit=True
    )
