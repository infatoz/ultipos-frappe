import frappe

def outlet_permission_query(user):
    """
    Permission Query for Outlet
    Controls which outlets a user can SEE
    """
    roles = frappe.get_roles(user)

    # 1. System Manager: God mode, sees everything
    if "System Manager" in roles:
        return "1=1"

    conditions = []

    # 2. Restaurant Owner: Sees all outlets linked to the restaurants they own
    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            restaurants_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
            conditions.append(f"restaurant IN ({restaurants_str})")

    # 3. Outlet Manager: Sees ONLY the outlet where their name is in the 'outlet_manager' field
    if "Outlet Manager" in roles:
        conditions.append(f"outlet_manager = {frappe.db.escape(user)}")

    # Apply conditions if any matched
    if conditions:
        return " OR ".join(conditions)

    # 4. Fallback: Show nothing
    return "1=0"