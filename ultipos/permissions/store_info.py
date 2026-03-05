import frappe

def get_permission_query_conditions(user):
    """
    SQL injection for the List View. 
    Hides other stores' info from the Outlet Manager.
    """
    if not user:
        user = frappe.session.user

    # System Managers and Admins see everything
    if "System Manager" in frappe.get_roles(user):
        return None

    # Check the User profile for their assigned outlet
    my_outlet = frappe.db.get_value("User", user, "outlet")

    # If they don't have an outlet assigned, lock them out
    if not my_outlet:
        return "`tabStore Info`.name = 'LOCKED'"

    # 🎯 THE SHIELD: Only show the Store Info linked to their specific Outlet
    return f"`tabStore Info`.outlet = '{my_outlet}'"


def has_permission(doc, ptype="read", user=None):
    """
    Document-level security. 
    Stops an Outlet Manager from saving details for a store they don't own.
    """
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return True

    my_outlet = frappe.db.get_value("User", user, "outlet")

    # If the document belongs to an outlet they don't own, block access!
    if doc.outlet and doc.outlet != my_outlet:
        return False 

    return True