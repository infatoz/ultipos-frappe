import frappe
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

@frappe.whitelist()
def sign(message):
    # Dynamically get the path to your private key
    key_path = frappe.get_app_path("ultipos", "public", "private-key.pem")
    
    if not os.path.exists(key_path):
        frappe.throw(f"Private key not found at {key_path}")

    with open(key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA1()
    )

    return base64.b64encode(signature).decode('utf-8')