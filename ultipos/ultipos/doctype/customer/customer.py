# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Customer(Document):
	pass

def get_or_create_customer(phone, data):
    customer = frappe.db.get_value("Customer", {"phone": phone}, "name")
    if customer:
        return customer

    doc = frappe.new_doc("Customer")
    doc.phone = phone
    doc.customer_name = data.get("name")
    doc.email = data.get("email")
    doc.whatsapp = phone
    doc.source = data.get("platform")
    doc.insert(ignore_permissions=True)
    return doc.name
