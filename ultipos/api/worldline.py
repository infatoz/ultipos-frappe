import requests
import frappe


@frappe.whitelist(allow_guest=True)
def create_worldline_payment(order_id):
    
    order = frappe.get_doc("Order", order_id)

    payload = {
        "orderId": order.name,
        "amount": int(order.grand_total * 100),
        "currency": "AUD",
        "redirectUrl": f"{frappe.utils.get_url()}/api/method/ultipos.api.payment.return_handler"
    }

    # 🔐 Call Worldline API here
    worldline_response = call_worldline(payload)

    order.worldline_reference = worldline_response["reference"]
    order.save(ignore_permissions=True)

    return {
        "redirect_url": worldline_response["redirectUrl"]
    }