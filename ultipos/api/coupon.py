import frappe
from frappe.utils import now_datetime, getdate


@frappe.whitelist(allow_guest=True)
def get_active(outlet_code):
    """
    ✅ Returns active coupons for an outlet
    Frontend expects list of coupons
    """
    if not outlet_code:
        frappe.throw("outlet_code required")

    outlet_name = frappe.db.get_value("Outlet", {"outlet_code": outlet_code}, "name")
    if not outlet_name:
        frappe.throw("Invalid outlet_code")

    today = getdate(now_datetime())

    coupons = frappe.get_all(
        "Coupon",
        filters={
            "status": "Active",
        },
        fields=[
            "name",
            "coupon_code",
            "discount_type",
            "discount_value",
            "min_order_amount",
            "max_discount",
            "start_date",
            "end_date",
            "outlet",
        ],
        order_by="modified desc",
    )

    result = []
    for c in coupons:
        # outlet restriction
        if c.get("outlet") and c.get("outlet") != outlet_name:
            continue

        # date validity
        if c.get("start_date") and today < getdate(c.get("start_date")):
            continue
        if c.get("end_date") and today > getdate(c.get("end_date")):
            continue

        result.append({
            "coupon_code": c.get("coupon_code"),
            "discount_type": c.get("discount_type"),
            "discount_value": c.get("discount_value"),
            "min_order_amount": c.get("min_order_amount"),
            "max_discount": c.get("max_discount"),
        })

    return result


@frappe.whitelist(allow_guest=True)
def validate_coupon(outlet_code, coupon_code, cart_total, customer_id=None):
    """
    ✅ Your existing validate_coupon (kept) - only minor safety fixes
    """
    if not outlet_code or not coupon_code:
        frappe.throw("outlet_code and coupon_code required")

    outlet_name = frappe.db.get_value("Outlet", {"outlet_code": outlet_code}, "name")
    if not outlet_name:
        frappe.throw("Invalid outlet_code")

    coupon_name = frappe.db.get_value(
        "Coupon",
        {"coupon_code": coupon_code, "status": "Active"},
        "name"
    )
    if not coupon_name:
        frappe.throw("Invalid coupon")

    coupon = frappe.get_doc("Coupon", coupon_name)

    # outlet restriction (if coupon.outlet is set)
    if coupon.outlet and coupon.outlet != outlet_name:
        frappe.throw("Coupon not applicable for this outlet")

    cart_total = float(cart_total or 0)

    if coupon.min_order_amount and cart_total < float(coupon.min_order_amount):
        frappe.throw("Minimum order not met")

    today = getdate(now_datetime())
    if coupon.start_date and today < getdate(coupon.start_date):
        frappe.throw("Coupon not started yet")
    if coupon.end_date and today > getdate(coupon.end_date):
        frappe.throw("Coupon expired")

    # per customer limit
    if customer_id and coupon.per_customer_limit:
        used_count = frappe.db.count(
            "Coupon Usage",
            filters={"coupon": coupon.name, "customer": customer_id}
        )
        if used_count >= int(coupon.per_customer_limit):
            frappe.throw("Coupon usage limit exceeded for customer")

    discount = 0
    if coupon.discount_type == "Percentage":
        discount = cart_total * float(coupon.discount_value or 0) / 100.0
    else:
        discount = float(coupon.discount_value or 0)

    # apply max discount
    if coupon.max_discount and discount > float(coupon.max_discount):
        discount = float(coupon.max_discount)

    discount = min(discount, cart_total)

    return {
        "valid": True,
        "discount": discount,
        "message": "Coupon applied successfully"
    }
