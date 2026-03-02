import frappe

def modifier_group_permission_query(user):
    """
    Permission Query for Modifier Group
    Controls which modifier groups an Outlet Manager can SEE
    """
    roles = frappe.get_roles(user)

    if "System Manager" in roles:
        return "1=1"

    conditions = []

    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            r_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
            conditions.append(f"restaurant IN ({r_str})")

    if "Outlet Manager" in roles:
        # Find the restaurant this outlet manager belongs to
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, fields=["restaurant"])
        if managed_outlets:
            r_names = list(set([o.restaurant for o in managed_outlets if o.restaurant]))
            if r_names:
                r_str = ", ".join([frappe.db.escape(r) for r in r_names])
                # Filter ONLY by restaurant, ignoring the outlet
                conditions.append(f"restaurant IN ({r_str})")

    if conditions:
        return " OR ".join(conditions)

    return "1=0"