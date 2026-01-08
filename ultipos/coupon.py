import frappe
from datetime import date

def validate_coupon(
    coupon_code,
    restaurant,
    outlet,
    customer,
    cart_total,
    order_type,
    platform="Web"
):
    coupon = frappe.get_doc(
        "Coupon",
        {"coupon_code": coupon_code, "status": "Active"}
    )

    today = date.today()

    if not (coupon.start_date <= today <= coupon.end_date):
        frappe.throw("Coupon expired")

    if coupon.restaurant != restaurant:
        frappe.throw("Invalid coupon")

    if coupon.outlet and coupon.outlet != outlet:
        frappe.throw("Coupon not valid for this outlet")

    if coupon.platform and coupon.platform != platform:
        frappe.throw("Coupon not valid on this platform")

    if coupon.min_order_amount and cart_total < coupon.min_order_amount:
        frappe.throw("Minimum order not met")

    used_count = frappe.db.count(
        "Coupon Usage",
        {"coupon": coupon.name, "customer": customer}
    )

    if coupon.per_customer_limit and used_count >= coupon.per_customer_limit:
        frappe.throw("Coupon already used")

    # Calculate discount
    if coupon.discount_type == "Percentage":
        discount = cart_total * coupon.discount_value / 100
    else:
        discount = coupon.discount_value

    if coupon.max_discount:
        discount = min(discount, coupon.max_discount)

    return {
        "coupon": coupon.name,
        "discount": discount
    }
