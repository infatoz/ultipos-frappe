import frappe

def outlet_permission_query(user):
    """
    Permission Query for Outlet
    Controls which outlets a user can SEE
    """
    roles = frappe.get_roles(user)

    # 1. System Manager sees everything
    if "System Manager" in roles:
        return "1=1"

    # 2. Find restaurants owned by this user
    owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")

    # 3. If they own restaurants, show outlets linked to those restaurants
    if owned_restaurants:
        # Format the list of restaurant names into a safe SQL 'IN' clause
        restaurants_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
        return f"restaurant IN ({restaurants_str})"

    # 4. Fallback: Show nothing
    return "1=0"