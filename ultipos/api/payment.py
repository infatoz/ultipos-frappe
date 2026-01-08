import frappe
from ultipos.api.worldline import worldline_create_payment


@frappe.whitelist(allow_guest=True)
def create_intent(outlet_code, amount, customer):
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code})

    settings = frappe.get_doc(
        "Worldline Settings",
        {"restaurant": outlet.restaurant, "is_enabled": 1}
    )

    redirect_url = worldline_create_payment(
        settings,
        amount,
        customer
    )

    return {
        "payment_gateway": "Worldline",
        "redirect_url": redirect_url
    }
