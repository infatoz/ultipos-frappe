import frappe

def outlet_permission_query(user):
    """
    Permission Query for Outlet
    Controls which outlets a user can SEE
    """

    # 'user' is automatically available in Permission Query scripts
    # Fetch roles for the current user manually to avoid the restricted frappe.get_roles attribute
    # roles = frappe.get_roles(user)

    # Manual Role Check Fallback
    user_roles = frappe.get_all("Has Role", filters={"parent": user}, fields=["role"])
    roles = [r.role for r in user_roles]

    # Get the restaurant linked to the logged-in user
    user_restaurant = frappe.db.get_value("User", user, "restaurant")

    # 1. System Manager: Sees everything
    if "System Manager" in roles:
        conditions = "1=1"

    # 2. Restaurant Owner: Filter by their linked restaurant
    elif user_restaurant:
        # We use frappe.db.escape to handle strings with quotes safely
        conditions = f"restaurant = {frappe.db.escape(user_restaurant)}"

    # 3. Fallback: Show nothing if they don't have a restaurant assigned
    else:
        conditions = "1=0"
        
    return conditions
