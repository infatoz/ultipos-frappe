import frappe

def user_permission_query(user):
    """
    Permission Query for User Doctype
    Controls which users someone can see in the User List
    """
    roles = frappe.get_roles(user)
    
    # System Managers see everyone
    if "System Manager" in roles:
        return "1=1"

    # Restaurant Owners only see themselves
    if "Restaurant Owner" in roles:
        return f"name = {frappe.db.escape(user)}"

    # Default fallback
    return f"name = {frappe.db.escape(user)}"