import frappe
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

@frappe.whitelist()
def qz_sign(data):
    """
    QZ Tray signing endpoint
    MUST return RAW STRING (not JSON)
    """

    # 🔑 Load private key
    private_key_path = frappe.get_site_path("private", "qz-private-key.pem")

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

    # ✍️ Sign data
    signature = private_key.sign(
        data.encode(),
        padding.PKCS1v15(),
        hashes.SHA512()
    )

    # ✅ QZ expects base64 string
    return base64.b64encode(signature).decode()
