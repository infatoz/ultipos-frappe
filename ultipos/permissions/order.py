import frappe

def order_permission_query(user):
    """
    Permission Query for Order
    Controls which orders users can SEE based on their role
    """
    roles = frappe.get_roles(user)

    # 1. System Manager sees all orders everywhere
    if "System Manager" in roles:
        return "1=1"

    conditions = []

    # 2. Restaurant Owner sees ONLY orders from their own restaurants
    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            r_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
            conditions.append(f"restaurant IN ({r_str})")

    # 3. Outlet Manager sees ONLY orders punched at their specific store
    if "Outlet Manager" in roles:
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, pluck="name")
        if managed_outlets:
            o_str = ", ".join([frappe.db.escape(o) for o in managed_outlets])
            conditions.append(f"outlet IN ({o_str})")

    # 4. 🎯 NEW: Order Manager sees ONLY orders for the Outlet saved in their User profile!
    if "OrderManager" in roles or "Order Manager" in roles:
        # We grab the custom 'outlet' field you created on the User DocType
        user_outlet = frappe.db.get_value("User", user, "outlet")
        if user_outlet:
            conditions.append(f"outlet = {frappe.db.escape(user_outlet)}")

    # Combine all valid conditions (If they have multiple roles, they get access to all of them)
    if conditions:
        return "(" + " OR ".join(conditions) + ")"

    # Fallback: If they don't match any of the above, block them completely
    return "1=0"