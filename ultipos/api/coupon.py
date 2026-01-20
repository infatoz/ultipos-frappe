# coupon.py:
import frappe
from frappe.utils import now_datetime, getdate


@frappe.whitelist(allow_guest=True)
def get_active(outlet_code=None):
    """
    ✅ Returns active coupons for outlet
    SAFE: selects only fields that exist in your Coupon DocType
    """
    if not outlet_code:
        frappe.throw("outlet_code required")

    outlet_name = frappe.db.get_value("Outlet", {"outlet_code": outlet_code}, "name")
    if not outlet_name:
        frappe.throw("Invalid outlet_code")

    today = getdate(now_datetime())

    coupons = frappe.get_all(
        "Coupon",
        filters={"status": "Active"},
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
            "platform",
            "applicable_order_type",
        ],
        order_by="modified desc",
    )

    result = []
    for c in coupons:
        # ✅ outlet restriction
        if c.get("outlet") and c.get("outlet") != outlet_name:
            continue

        # ✅ date validity
        if c.get("start_date") and today < getdate(c.get("start_date")):
            continue
        if c.get("end_date") and today > getdate(c.get("end_date")):
            continue

        result.append({
            "coupon_code": (c.get("coupon_code") or "").upper(),
            "discount_type": c.get("discount_type"),
            "discount_value": float(c.get("discount_value") or 0),

            "min_order_amount": float(c.get("min_order_amount") or 0),
            "max_discount": float(c.get("max_discount") or 0),

            "start_date": str(c.get("start_date") or ""),
            "end_date": str(c.get("end_date") or ""),

            "platform": c.get("platform"),
            "applicable_order_type": c.get("applicable_order_type"),
        })

    return result


@frappe.whitelist(allow_guest=True)
def validate_coupon(outlet_code=None, coupon_code=None, cart_total=0, customer_id=None):
    """
    ✅ validates and returns discount
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

    # ✅ outlet restriction
    if coupon.outlet and coupon.outlet != outlet_name:
        frappe.throw("Coupon not applicable for this outlet")

    cart_total = float(cart_total or 0)

    # ✅ min order check
    if coupon.min_order_amount and cart_total < float(coupon.min_order_amount):
        frappe.throw("Minimum order not met")

    # ✅ date validity
    today = getdate(now_datetime())
    if coupon.start_date and today < getdate(coupon.start_date):
        frappe.throw("Coupon not started yet")
    if coupon.end_date and today > getdate(coupon.end_date):
        frappe.throw("Coupon expired")

    # ✅ discount
    discount = 0
    if coupon.discount_type == "Percentage":
        discount = cart_total * float(coupon.discount_value or 0) / 100.0
    else:
        discount = float(coupon.discount_value or 0)

    # ✅ apply max discount
    if coupon.max_discount and float(coupon.max_discount) > 0:
        discount = min(discount, float(coupon.max_discount))

    discount = min(discount, cart_total)

    return {
        "valid": True,
        "discount": discount,
        "message": "Coupon applied successfully"
    }