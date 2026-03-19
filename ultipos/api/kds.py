import frappe

@frappe.whitelist()
def get_kds_data():
    """Fetches Printers and Active Tickets securely for the logged-in user's Outlet"""
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
            return {"error": "No outlet assigned to this user.", "printers": []}
    else:
        outlet_filter = ["in", permitted_outlets]

    # 2. 🎯 DYNAMIC PRINTERS: Fetch ONLY the printers assigned to THIS user's outlet!
    printers = frappe.get_all(
        "Printer", 
        filters={
            "is_active": 1, 
            "outlet": outlet_filter # This locks the dropdown!
        }, 
        fields=["name", "printer_name"]
    )

    # 3. Fetch Orders that are officially Accepted OR currently Preparing
    orders = frappe.get_all(
        "Order",
        filters={
            "outlet": outlet_filter,
            "order_status": ["in", ["Accepted", "Preparing"]] 
        },
        fields=["name", "order_number", "creation", "notes", "order_type"] 
    )

    if not orders:
        return {"orders": [], "items": [], "printers": printers}

    order_names = [o.name for o in orders]

    # 4. Get the actual food items for these orders that ARE NOT "Ready"
    items = frappe.get_all(
        "Order Item",
        filters={
            "parent": ["in", order_names],
            "item_status": ["!=", "Ready"]
        },
        fields=["name", "parent", "item_name", "menu_item", "qty", "item_status", "modifiers", "notes"]
    )
    
    # 5. MAP ITEMS TO PRINTERS: Look at the Menu Item to see where it should go
    for item in items:
        item.assigned_printers = []
        if item.menu_item:
            printer_configs = frappe.get_all("Item Printer Config", filters={"parent": item.menu_item}, fields=["printer"])
            item.assigned_printers = [p.printer for p in printer_configs]
        
        # Fallback for small stores
        if not item.assigned_printers:
            item.assigned_printers = ["Main Station"]

    # Filter out any orders where ALL items are already "Ready"
    active_order_names = [i.parent for i in items]
    active_orders = [o for o in orders if o.name in active_order_names]

    for o in active_orders:
        o.order_time = o.creation.strftime("%I:%M %p") if o.creation else ""

    return {"orders": active_orders, "items": items, "printers": printers}


@frappe.whitelist()
def update_item_status(item_docname, new_status):
    """Updates the status when the chef taps the item, and magically syncs the Main Order!"""
    frappe.db.set_value("Order Item", item_docname, "item_status", new_status)
    
    parent_order = frappe.db.get_value("Order Item", item_docname, "parent")
    all_items = frappe.get_all("Order Item", filters={"parent": parent_order}, fields=["item_status"])
    
    total_items = len(all_items)
    ready_items = sum(1 for i in all_items if i.item_status == "Ready")
    preparing_items = sum(1 for i in all_items if i.item_status == "Preparing")
    
    if ready_items == total_items:
        frappe.db.set_value("Order", parent_order, "order_status", "Ready")
    elif preparing_items > 0 or ready_items > 0:
        frappe.db.set_value("Order", parent_order, "order_status", "Preparing")
        
    frappe.db.commit()
    return "Success"