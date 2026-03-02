import frappe

def restaurant_permission_query(user):
    """
    Permission Query for Restaurant
    Controls which restaurants a user can SEE
    """
    roles = frappe.get_roles(user)

    # 1. System Manager sees everything
    if "System Manager" in roles:
        return "1=1"

    conditions = []

    # 2. Restaurant Owner only sees records where they are the owner_user
    if "Restaurant Owner" in roles:
        conditions.append(f"owner_user = {frappe.db.escape(user)}")

    # 3. Outlet Manager sees the restaurant their assigned outlet belongs to
    if "Outlet Manager" in roles:
        # Find the outlets this user manages and get the parent restaurant name
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, fields=["restaurant"])
        
        if managed_outlets:
            # Extract the unique restaurant names and format them for the SQL query
            r_names = list(set([o.restaurant for o in managed_outlets if o.restaurant]))
            if r_names:
                r_str = ", ".join([frappe.db.escape(r) for r in r_names])
                conditions.append(f"name IN ({r_str})")

    # Apply conditions if any matched
    if conditions:
        return " OR ".join(conditions)

    # Fallback
    return "1=0"