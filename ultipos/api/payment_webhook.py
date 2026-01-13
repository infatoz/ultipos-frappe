import frappe

@frappe.whitelist(allow_guest=True)
def worldline_webhook():
    payload = frappe.request.get_json()

    order_id = payload.get("order_id")
    status = payload.get("status")

    order = frappe.get_doc("Order", order_id, ignore_permissions=True)

    if status == "SUCCESS":
        order.payment_status = "Paid"
        order.order_status = "Accepted"
    else:
        order.payment_status = "Failed"

    order.save(ignore_permissions=True)
    frappe.db.commit()

    return "OK"

@frappe.whitelist(allow_guest=True)
def return_handler():
    order_id = frappe.form_dict.get("orderId")
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = f"/order-status/{order_id}"

    data = frappe.form_dict
    order_id = data.get("orderId")
    status = data.get("status")

    order = frappe.get_doc("Order", order_id)

    if status == "SUCCESS":
        order.status = "PAID"
    else:
        order.status = "FAILED"

    order.save(ignore_permissions=True)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = f"/order-status/{order_id}"