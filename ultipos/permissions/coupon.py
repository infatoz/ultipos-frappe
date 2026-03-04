import frappe

def get_permission_query_conditions(user):
    """
    SQL injection for the List View. 
    This hides Outlet 2's coupons from Outlet 1's manager table.
    """
    if not user:
        user = frappe.session.user

    # System Managers and Admins see everything
    if "System Manager" in frappe.get_roles(user):
        return None

    # 1. Figure out which Outlets this user is allowed to manage
    # (Assuming you use standard Frappe User Permissions to link Users to Outlets)
    permitted_outlets = frappe.permissions.get_user_permissions(user).get("Outlet", [])
    
    # Optional: If you use a custom field on the User profile instead, you would do this:
    # my_outlet = frappe.db.get_value("User", user, "custom_outlet_field")
    # permitted_outlets = [my_outlet] if my_outlet else []

    if not permitted_outlets:
        # If they don't have an outlet assigned, show them absolutely nothing!
        return "`tabCoupon`.name = 'LOCKED'"

    # Format the outlets for the SQL query: 'MTR Outlet1', 'MTR Outlet2'
    outlet_list = ",".join([f"'{o}'" for o in permitted_outlets])

    # 🎯 THE SHIELD: Show coupons belonging to their outlet, OR global coupons (blank outlet)
    return f"(`tabCoupon`.outlet IN ({outlet_list}) OR `tabCoupon`.outlet IS NULL OR `tabCoupon`.outlet = '')"


def has_permission(doc, ptype="read", user=None):
    """
    Document-level security. 
    Stops a manager from editing/saving a coupon they don't own.
    """
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return True

    permitted_outlets = frappe.permissions.get_user_permissions(user).get("Outlet", [])

    # If the coupon is assigned to an outlet, check if the user manages that outlet
    if doc.outlet:
        if doc.outlet not in permitted_outlets:
            return False # ⛔ Block Access
            
    # Optional: Prevent normal managers from editing/creating Global Coupons
    if not doc.outlet and ptype in ["write", "create", "delete"]:
        return False

    return True