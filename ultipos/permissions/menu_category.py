import frappe

def menu_category_permission_query(user):
    """
    Permission Query for Menu Category
    Controls which categories a user can SEE based on the parent Menu
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
            # Find all menus linked to these restaurants
            menus = frappe.get_all("Menu", filters={"restaurant": ["in", owned_restaurants]}, pluck="name")
            allowed_menus.extend(menus)

    # 3. Get menus for Outlet Manager
    if "Outlet Manager" in roles:
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, pluck="name")
        if managed_outlets:
            # Find all menus linked to these outlets
            menus = frappe.get_all("Menu", filters={"outlet": ["in", managed_outlets]}, pluck="name")
            allowed_menus.extend(menus)

    # 4. Filter the Categories by the allowed Menus
    if allowed_menus:
        # Remove duplicates just to be safe
        unique_menus = list(set(allowed_menus))
        m_str = ", ".join([frappe.db.escape(m) for m in unique_menus])
        
        # NOTE: This assumes your link field is named 'menu' on the Menu Category DocType. 
        # If you named it something else (like 'parent_menu'), change 'menu IN' below!
        return f"menu IN ({m_str})"

    # Fallback
    return "1=0"