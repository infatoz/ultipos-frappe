import frappe

def get_permission_query_conditions(user):
    """
    SQL injection for the List View. 
    Reads directly from the User profile to isolate Stripe Settings.
    """
    if not user:
        user = frappe.session.user

    # System Managers and Admins see everything
    if "System Manager" in frappe.get_roles(user):
        return None

    # 1. Check if the User profile has a direct 'restaurant' field
    my_restaurant = frappe.db.get_value("User", user, "restaurant")

    # 2. If no direct restaurant field, check if they have an 'outlet' field instead
    if not my_restaurant:
        my_outlet = frappe.db.get_value("User", user, "outlet")
        if my_outlet:
            # Look up the restaurant that owns this outlet
            my_restaurant = frappe.db.get_value("Outlet", my_outlet, "restaurant")

    # 3. If we STILL can't find a restaurant for this user, lock it down
    if not my_restaurant:
        return "`tabStripe Settings`.name = 'LOCKED'"

    # 🎯 THE SHIELD: Only show rows matching their exact Restaurant
    return f"`tabStripe Settings`.restaurant = '{my_restaurant}'"


def has_permission(doc, ptype="read", user=None):
    """
    Document-level security. 
    Stops the MTR owner from editing GRB's Stripe keys if they guess the URL.
    """
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return True

    # Figure out the user's restaurant exactly like we did above
    my_restaurant = frappe.db.get_value("User", user, "restaurant")
    
    if not my_restaurant:
        my_outlet = frappe.db.get_value("User", user, "outlet")
        if my_outlet:
            my_restaurant = frappe.db.get_value("Outlet", my_outlet, "restaurant")

    # If the document belongs to a restaurant they don't own, block access
    if doc.restaurant and doc.restaurant != my_restaurant:
        return False # ⛔ Block Access

    return True