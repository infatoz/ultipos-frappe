import frappe

@frappe.whitelist(allow_guest=True)
def create_or_update(phone, name=None, email=None):
    customer = frappe.db.get_value(
        "Customer",
        {"phone": phone},
        "name"
    )

    if customer:
        doc = frappe.get_doc("Customer", customer)
    else:
        doc = frappe.new_doc("Customer")
        doc.phone = phone

    doc.customer_name = name
    doc.email = email
    doc.save(ignore_permissions=True)

    return {"customer_id": doc.name}
