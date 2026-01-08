import frappe

def restaurant_permission_query(user):
    """
    Permission Query for Restaurant
    Only assigned Restaurant Owner can see their restaurant
    """

    # System User (UltiPOS Admin) → see all
    user_roles = frappe.get_all("Has Role", filters={"parent": user}, fields=["role"])
    roles = [r.role for r in user_roles]
    
    if "System Manager" in roles:
        return "1=1"

    # Get restaurant assigned to logged-in user
    user_restaurant = frappe.db.get_value("User", user, "restaurant")
    print("user_restaurant", user_restaurant)

    # Restaurant Owner → only their restaurant
    if user_restaurant:
        return f"name = {frappe.db.escape(user_restaurant)}"

    # No restaurant assigned → see nothing
    return "1=0"
