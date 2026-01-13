import frappe


@frappe.whitelist(allow_guest=True)
def create_or_update(phone, name=None, email=None):
    if not phone:
        frappe.throw("phone required")

    customer_name = frappe.db.get_value("Customer", {"phone": phone}, "name")

    if customer_name:
        doc = frappe.get_doc("Customer", customer_name)
    else:
        doc = frappe.new_doc("Customer")
        doc.phone = phone
        doc.source = "UltiPOS"

    if name:
        doc.customer_name = name
    if email:
        doc.email = email

    doc.save(ignore_permissions=True)

    return {"customer_id": doc.name}
