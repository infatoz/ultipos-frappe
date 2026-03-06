import frappe

@frappe.whitelist()
def get_kds_tickets():
    """Fetches active items strictly for the logged-in user's assigned Outlet"""
    user = frappe.session.user
    
    # 1. Ask Frappe's official permission system which Outlets this user owns
    permitted_outlets = frappe.permissions.get_user_permissions(user).get("Outlet", [])
    
    if not permitted_outlets:
        custom_outlet = frappe.db.get_value("User", user, "outlet")
        if custom_outlet:
            permitted_outlets = [custom_outlet]

    if not permitted_outlets:
        if "System Manager" in frappe.get_roles(user):
            outlet_filter = ["!=", ""]
        else:
            return {"error": "No outlet assigned to this user."}
    else:
        outlet_filter = ["in", permitted_outlets]

    # 2. Fetch Orders that are officially Accepted (Paid/COD) OR currently Preparing
    orders = frappe.get_all(
        "Order",
        filters={
            "outlet": outlet_filter,
            "order_status": ["in", ["Accepted", "Preparing"]] 
        },
        fields=["name", "order_number", "creation", "notes"] 
    )

    if not orders:
        return {"orders": [], "items": []}

    order_names = [o.name for o in orders]

    # 3. Get the actual food items for these orders that ARE NOT "Ready"
    items = frappe.get_all(
        "Order Item",
        filters={
            "parent": ["in", order_names],
            "item_status": ["!=", "Ready"]
        },
        fields=["name", "parent", "item_name", "qty", "item_status", "printer", "modifiers", "notes"]
    )

    # 4. Filter out any orders where ALL items are already "Ready"
    active_order_names = [i.parent for i in items]
    active_orders = [o for o in orders if o.name in active_order_names]

    # Rename 'creation' to 'order_time' so the HTML displays it correctly
    for o in active_orders:
        o.order_time = o.creation.strftime("%I:%M %p") if o.creation else ""

    return {"orders": active_orders, "items": items}

@frappe.whitelist()
def update_item_status(item_docname, new_status):
    """Updates the status when the chef taps the item, and magically syncs the Main Order!"""
    # 1. Update the specific dish
    frappe.db.set_value("Order Item", item_docname, "item_status", new_status)
    
    # 2. Find out which Order this dish belongs to
    parent_order = frappe.db.get_value("Order Item", item_docname, "parent")
    
    # 3. Look at ALL the dishes in this order to see how the kitchen is doing
    all_items = frappe.get_all("Order Item", filters={"parent": parent_order}, fields=["item_status"])
    
    total_items = len(all_items)
    ready_items = sum(1 for i in all_items if i.item_status == "Ready")
    preparing_items = sum(1 for i in all_items if i.item_status == "Preparing")
    
    # 4. 🎯 THE MAGIC SYNC LOGIC
    if ready_items == total_items:
        # If EVERY dish is Ready, mark the whole Order as Ready!
        frappe.db.set_value("Order", parent_order, "order_status", "Ready")
    elif preparing_items > 0 or ready_items > 0:
        # If at least one dish is cooking, mark the whole Order as Preparing!
        frappe.db.set_value("Order", parent_order, "order_status", "Preparing")
        
    return "Success"