import frappe

@frappe.whitelist(allow_guest=True)
def get(outlet_code=None):
    """
    Public API to fetch Store Info for the frontend modal/footer.
    """
    if not outlet_code:
        frappe.throw("outlet_code is required")

    # 1. Look up the exact Outlet document name using the code provided by React
    outlet_name = frappe.db.get_value("Outlet", {"outlet_code": outlet_code}, "name")
    
    if not outlet_name:
        frappe.throw(f"Outlet with code {outlet_code} not found")

    # 2. Fetch the Store Info linked to this specific outlet
    store_info = frappe.get_all(
        "Store Info",
        filters={"outlet": outlet_name},
        fields=[
            "phone_number", 
            "email", 
            "address", 
            "about_us", 
            "privacy_policy", 
            "terms_and_conditions"
        ],
        limit=1
    )

    # 3. If the Outlet Manager hasn't filled it out yet, return empty strings so React doesn't crash
    if not store_info:
        return {
            "phone_number": "",
            "email": "",
            "address": "",
            "about_us": "",
            "privacy_policy": "",
            "terms_and_conditions": ""
        }

    # 4. Return the data to the frontend!
    # Inject the actual restaurant name so the modal header looks professional
    store_info[0]["storeName"] = frappe.db.get_value("Outlet", outlet_name, "restaurant")
    return store_info[0]