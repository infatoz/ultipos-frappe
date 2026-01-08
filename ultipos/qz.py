import frappe
import hashlib

@frappe.whitelist(allow_guest=True)
def sign(data):
    secret = frappe.conf.qz_secret
    return hashlib.sha256((data + secret).encode()).hexdigest()
