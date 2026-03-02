import frappe

def modifier_option_permission_query(user):
    """
    Permission Query for Modifier Option
    Controls which options an Outlet Manager can SEE by tracing back to the Modifier Group
    """
    roles = frappe.get_roles(user)

    if "System Manager" in roles:
        return "1=1"

    allowed_groups = []

    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            groups = frappe.get_all("Modifier Group", filters={"restaurant": ["in", owned_restaurants]}, pluck="name")
            allowed_groups.extend(groups)

    if "Outlet Manager" in roles:
        # 1. Find the restaurant this outlet manager belongs to
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, fields=["restaurant"])
        if managed_outlets:
            r_names = list(set([o.restaurant for o in managed_outlets if o.restaurant]))
            if r_names:
                # 2. Find all Modifier Groups attached to that Restaurant
                groups = frappe.get_all("Modifier Group", filters={"restaurant": ["in", r_names]}, pluck="name")
                allowed_groups.extend(groups)

    if allowed_groups:
        unique_groups = list(set(allowed_groups))
        g_str = ", ".join([frappe.db.escape(g) for g in unique_groups])
        
        # NOTE: Assumes your link field is called 'modifier_group'
        return f"modifier_group IN ({g_str})"

    return "1=0"