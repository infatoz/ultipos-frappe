import frappe

@frappe.whitelist(allow_guest=True)
def mark_paid(order_id):
    order = frappe.get_doc("Order", order_id)

    if order.payment_status == "Paid":
        return {"ok": True, "already_paid": True}

    order.payment_status = "Paid"
    order.status = "PAID"
    order.save(ignore_permissions=True)

    frappe.db.set_value(
        "Order Payment",
        {"order": order_id},
        "status",
        "Paid"
    )

    return {"ok": True, "order_id": order_id}
