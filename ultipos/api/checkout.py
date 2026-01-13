import frappe
from ultipos.api.utils import _loads, get_outlet
from ultipos.api.coupon import validate_coupon


@frappe.whitelist(allow_guest=True)
def preview(outlet_code, items, coupon_code=None, customer_id=None):
    outlet = get_outlet(outlet_code)

    items = _loads(items) or []
    if not isinstance(items, list) or not items:
        frappe.throw("items list required")

    subtotal = 0
    for i in items:
        subtotal += float(i.get("price") or 0) * int(i.get("qty") or 0)

    discount = 0
    if coupon_code:
        discount = validate_coupon(outlet_code, coupon_code, subtotal, customer_id)["discount"]

    tax = 0
    delivery_fee = 0

    grand_total = subtotal + tax + delivery_fee - discount

    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "delivery_fee": delivery_fee,
        "grand_total": grand_total
    }


# ✅ ADD THIS FUNCTION (THIS FIXES YOUR 417 ERROR)
@frappe.whitelist(allow_guest=True)
def create_or_update(phone=None, name=None, email=None):
    phone = (phone or "").strip()
    name = (name or "").strip()
    email = (email or "").strip()

    if not phone:
        frappe.throw("phone is required")

    # ✅ Customer DocType must exist
    # If your DocType name is different, tell me, I will update it.
    existing = frappe.get_all(
        "Customer",
        filters={"phone": phone},
        pluck="name",
        limit=1
    )

    if existing:
        customer_id = existing[0]
        doc = frappe.get_doc("Customer", customer_id)

        # update fields safely
        if name:
            if hasattr(doc, "customer_name"):
                doc.customer_name = name
            elif hasattr(doc, "name1"):
                doc.name1 = name

        if email and hasattr(doc, "email"):
            doc.email = email

        doc.save(ignore_permissions=True)
        return {"customer_id": doc.name}

    # create new
    doc = frappe.new_doc("Customer")

    if hasattr(doc, "customer_name"):
        doc.customer_name = name or phone
    elif hasattr(doc, "name1"):
        doc.name1 = name or phone

    if hasattr(doc, "phone"):
        doc.phone = phone
    if hasattr(doc, "email"):
        doc.email = email

    doc.insert(ignore_permissions=True)
    return {"customer_id": doc.name}
