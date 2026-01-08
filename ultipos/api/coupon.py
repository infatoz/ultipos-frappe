import frappe

@frappe.whitelist(allow_guest=True)
def validate(outlet_code, coupon_code, cart_total, customer_id):
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code})

    coupon = frappe.get_doc(
        "Coupon",
        {
            "coupon_code": coupon_code,
            "outlet": outlet.name,
            "status": "Active"
        }
    )

    if cart_total < coupon.min_order_amount:
        frappe.throw("Minimum order not met")

    discount = (
        cart_total * coupon.discount_value / 100
        if coupon.discount_type == "Percentage"
        else coupon.discount_value
    )

    return {
        "valid": True,
        "discount": discount
    }
