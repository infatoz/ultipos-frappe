import frappe

def get_permission_query_conditions(user):
    """Secures list views and API fetches. Injects SQL to hide other owners' data."""
    if not user:
        user = frappe.session.user
        
    if "System Manager" in frappe.get_roles(user):
        return None

    # 🎯 THE FIX: Changed "owner" to "owner_user"
    restaurant = frappe.db.get_value("Restaurant", {"owner_user": user}, "name") 
    
    if restaurant:
        return f"`tabPromotion`.restaurant = '{restaurant}'"
    
    return "1=2"

def has_permission(doc, ptype="read", user=None):
    """Secures direct document access."""
    if not user:
        user = frappe.session.user
        
    if "System Manager" in frappe.get_roles(user):
        return True

    # 🎯 THE FIX: Changed "owner" to "owner_user"
    restaurant = frappe.db.get_value("Restaurant", {"owner_user": user}, "name")
    
    if restaurant and doc.restaurant == restaurant:
        return True
        
    return False