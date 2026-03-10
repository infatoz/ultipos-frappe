import frappe
from frappe.utils import now

@frappe.whitelist()
def get_dashboard_data():
    user = frappe.session.user
    
    permitted_outlets = frappe.permissions.get_user_permissions(user).get("Outlet", [])
    if not permitted_outlets:
        custom_outlet = frappe.db.get_value("User", user, "outlet")
        if custom_outlet: permitted_outlets = [custom_outlet]

    if not permitted_outlets: return {"error": "No outlet assigned."}
    my_outlet = permitted_outlets[0]
    
    outlet_settings = frappe.db.get_value("Outlet", my_outlet, ["is_accepting_orders", "auto_accept_orders", "outlet_name"], as_dict=True)

    shift_start = frappe.cache().hget("shift_start_times", frappe.session.sid)
    if not shift_start:
        shift_start = now()
        frappe.cache().hset("shift_start_times", frappe.session.sid, shift_start)

    orders = frappe.get_all(
        "Order",
        filters={
            "outlet": my_outlet,
            "creation": [">=", shift_start] 
        },
        fields=["name", "order_number", "order_status", "payment_status", "total_amount", "creation", "order_type"],
        order_by="creation desc"
    )

    # 🎯 NEW: Fetch all the food items for these orders!
    order_names = [o.name for o in orders]
    all_items = []
    if order_names:
        all_items = frappe.get_all(
            "Order Item",
            filters={"parent": ["in", order_names]},
            fields=["parent", "item_name", "qty", "modifiers"]
        )

    for o in orders:
        o.order_time = o.creation.strftime("%I:%M %p")
        customer_doc = frappe.get_all("Order Customer", filters={"parent": o.name}, fields=["name1"], limit=1)
        o.customer_name = customer_doc[0].name1 if customer_doc else "Guest"
        
        # 🎯 NEW: Attach the items to this specific order so React can read them
        o.items = [item for item in all_items if item.parent == o.name]

    return {
        "outlet": my_outlet,
        "settings": outlet_settings,
        "orders": orders
    }
@frappe.whitelist()
def update_order_status(order_id, new_status):
    """FOH Accepts or Declines an order"""
    frappe.db.set_value("Order", order_id, "order_status", new_status)
    
    # If declined, cancel the items so KDS never sees them
    if new_status == "Cancelled":
        items = frappe.get_all("Order Item", filters={"parent": order_id}, pluck="name")
        for item in items:
            frappe.db.set_value("Order Item", item, "item_status", "Cancelled")
            
    return "Success"

@frappe.whitelist()
def toggle_setting(outlet, field, value):
    """Toggles Is Active or Auto Accept"""
    frappe.db.set_value("Outlet", outlet, field, int(value))
    return "Success"