import frappe

def user_permission_query(user):
    """
    Permission Query for User Doctype
    Controls which users someone can see in the User List
    """
    roles = frappe.get_roles(user)
    
    # 1. System Managers see everyone
    if "System Manager" in roles:
        return "1=1"

    # 2. Base condition: Everyone can always see their own profile
    conditions = [f"name = {frappe.db.escape(user)}"]

    # 3. Restaurant Owners can ALSO see anyone linked to their restaurant
    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            r_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
            # This looks at the custom "restaurant" field you added to the User form!
            conditions.append(f"restaurant IN ({r_str})")

    return " OR ".join(conditions)