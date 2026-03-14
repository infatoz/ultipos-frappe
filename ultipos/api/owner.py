import frappe
from frappe.utils import today, add_days

@frappe.whitelist()
def get_dashboard_stats(period="This Month", outlet_filter="All"):
    user = frappe.session.user
    roles = frappe.get_roles(user)

    # 1. 🛡️ SECURITY: Only Owners and Admins can see this!
    if "Restaurant Owner" not in roles and "System Manager" not in roles:
        return {"error": "Unauthorized. You must be a Restaurant Owner."}

    # 2. 📅 DATE FILTERS
    end_date = today()
    if period == "Today":
        start_date = today()
    elif period == "This Week":
        start_date = add_days(today(), -7)
    else: # This Month
        start_date = add_days(today(), -30)

    # 3. 🏢 FIND THEIR EMPIRE
    if "System Manager" in roles:
        restaurants = frappe.get_all("Restaurant", pluck="name")
    else:
        restaurants = frappe.get_all("Restaurant", filters={"owner_user": user}, pluck="name")

    if not restaurants:
        return {"error": "No restaurants assigned to your account."}

    all_outlets = frappe.get_all("Outlet", filters={"restaurant": ["in", restaurants]}, fields=["name", "outlet_name"])
    if not all_outlets:
        return {"error": "No outlets found under your restaurants."}

    # 4. 💸 FETCH THE MONEY (Only Successful Paid Orders)
    filters = {
        "restaurant": ["in", restaurants],
        "creation": ["between", [start_date + " 00:00:00", end_date + " 23:59:59"]],
        "order_status": ["!=", "Cancelled"],
        "payment_status": "Paid"
    }
    if outlet_filter != "All":
        filters["outlet"] = outlet_filter

    orders = frappe.get_all("Order", filters=filters, fields=["name", "outlet", "total_amount"])

    # 5. 📊 CRUNCH THE NUMBERS
    total_sales = sum(o.total_amount for o in orders)
    
    # Create a scoreboard
    outlet_stats = {o.name: {"name": o.outlet_name or o.name, "sales": 0, "orders": 0} for o in all_outlets}
    for o in orders:
        if o.outlet in outlet_stats:
            outlet_stats[o.outlet]["sales"] += o.total_amount
            outlet_stats[o.outlet]["orders"] += 1

    # Sort the leaderboard from highest sales to lowest
    ranked = sorted(outlet_stats.values(), key=lambda x: x["sales"], reverse=True)
    
    best_outlet = ranked[0]["name"] if ranked and ranked[0]["sales"] > 0 else "None yet"
    worst_outlet = ranked[-1]["name"] if ranked and ranked[-1]["sales"] >= 0 and len(ranked) > 1 else "None yet"

    return {
        "total_sales": total_sales,
        "total_orders": len(orders),
        "best_outlet": best_outlet,
        "worst_outlet": worst_outlet,
        "ranked_outlets": ranked,
        "available_outlets": all_outlets
    }