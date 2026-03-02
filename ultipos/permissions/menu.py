import frappe

def menu_permission_query(user):
    """
    Permission Query for Menu Doctype
    Controls which menus a user can SEE
    """
    roles = frappe.get_roles(user)

    # 1. System Manager: God mode, sees everything
    if "System Manager" in roles:
        return "1=1"

    conditions = []

    # 2. Restaurant Owner: Sees all menus linked to restaurants they own
    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            r_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
            conditions.append(f"restaurant IN ({r_str})")

    # 3. Outlet Manager: Sees ONLY menus assigned to the outlets they manage
    if "Outlet Manager" in roles:
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, pluck="name")
        if managed_outlets:
            o_str = ", ".join([frappe.db.escape(o) for o in managed_outlets])
            conditions.append(f"outlet IN ({o_str})")

    # Apply conditions if any matched
    if conditions:
        return " OR ".join(conditions)

    # 4. Fallback: Show nothing
    return "1=0"