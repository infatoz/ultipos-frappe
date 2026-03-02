import frappe

def printer_permission_query(user):
    """
    Permission Query for Printer
    Controls which printers an Outlet Manager can SEE
    """
    roles = frappe.get_roles(user)

    # 1. System Manager sees all hardware
    if "System Manager" in roles:
        return "1=1"

    conditions = []

    # 2. Restaurant Owner sees all printers in their company
    if "Restaurant Owner" in roles:
        owned_restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")
        if owned_restaurants:
            r_str = ", ".join([frappe.db.escape(r) for r in owned_restaurants])
            conditions.append(f"restaurant IN ({r_str})")

    # 3. Outlet Manager sees ONLY printers sitting in their specific store
    if "Outlet Manager" in roles:
        managed_outlets = frappe.get_all("Outlet", filters={"outlet_manager": user}, pluck="name")
        if managed_outlets:
            o_str = ", ".join([frappe.db.escape(o) for o in managed_outlets])
            conditions.append(f"outlet IN ({o_str})")

    if conditions:
        return " OR ".join(conditions)

    # Fallback
    return "1=0"