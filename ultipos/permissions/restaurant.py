import frappe

def restaurant_permission_query(user):
    """
    Permission Query for Restaurant
    Only assigned Restaurant Owner can see their restaurant
    """
    roles = frappe.get_roles(user)
    
    # System Manager sees everything
    if "System Manager" in roles:
        return "1=1"

    # Restaurant Owner only sees records where they are the owner_user
    if "Restaurant Owner" in roles:
        return f"owner_user = {frappe.db.escape(user)}"

    # Fallback
    return "1=0"