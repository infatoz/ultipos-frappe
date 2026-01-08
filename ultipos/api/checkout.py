import frappe
from ultipos.api.utils import validate_coupon

@frappe.whitelist(allow_guest=True)
def preview(outlet_code, items, coupon_code=None):
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code})

    subtotal = sum(i["price"] * i["qty"] for i in items)

    discount = 0
    if coupon_code:
        discount = validate_coupon(
            outlet_code,
            coupon_code,
            subtotal,
            None
        )["discount"]

    tax = subtotal * outlet.tax_percent / 100
    total = subtotal + tax - discount

    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "grand_total": total
    }

