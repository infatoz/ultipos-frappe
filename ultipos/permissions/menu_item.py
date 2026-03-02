import frappe

def menu_item_permission_query(user):
    """
    Permission Query for Menu Item
    Controls which items an Outlet Manager can SEE by tracing back to the Menu
    """
    roles = frappe.get_roles(user)

    # 1. System Manager sees everything
    if "System Manager" in roles:
        return "1=1"

    allowed_menus = []

    # 2. Get menus for Restaurant Owner
    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            menus = frappe.get_all("Menu", filters={"restaurant": ["in", owned_restaurants]}, pluck="name")
            allowed_menus.extend(menus)

    # 3. Get menus for Outlet Manager
    if "Outlet Manager" in roles:
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, pluck="name")
        if managed_outlets:
            menus = frappe.get_all("Menu", filters={"outlet": ["in", managed_outlets]}, pluck="name")
            allowed_menus.extend(menus)

    # 4. Filter the Items by tracing through the Categories
    if allowed_menus:
        # Get all Categories linked to the allowed Menus
        allowed_categories = frappe.get_all("Menu Category", filters={"menu": ["in", allowed_menus]}, pluck="name")
        
        if allowed_categories:
            unique_categories = list(set(allowed_categories))
            c_str = ", ".join([frappe.db.escape(c) for c in unique_categories])
            
            # FIXED: Changed from 'menu_category IN' to 'category IN'
            return f"category IN ({c_str})"

    # Fallback
    return "1=0"