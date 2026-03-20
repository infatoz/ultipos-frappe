import frappe
import json

@frappe.whitelist()
def get_campaign_data():
    """Fetches outlets and customers for the logged-in owner's portal"""
    if frappe.session.user == "Guest":
        frappe.throw("Not logged in", frappe.PermissionError)

    restaurant = frappe.db.get_value("Restaurant", {"owner_user": frappe.session.user}, "name")
    
    if not restaurant:
        return {"success": False, "message": "No restaurant assigned to this user."}

    # 🎯 THE FIX: Added ignore_permissions=True to bypass Frappe Role blocks
    outlets = frappe.get_all(
        "Outlet", 
        filters={"restaurant": restaurant}, 
        fields=["name", "outlet_name"],
        ignore_permissions=True
    )
    
    customers = frappe.get_all(
        "Customer", 
        filters={"custom_restaurant": restaurant}, 
        # 🎯 THE FIX: Changed to "phone" and "email"
        fields=["name", "customer_name", "phone", "email"], 
        ignore_permissions=True
    )
    
    return {"success": True, "restaurant": restaurant, "outlets": outlets, "customers": customers}
@frappe.whitelist()
def dispatch_campaign(title, channel, target_audience, message, restaurant, outlet=None, specific_customers=None):
    """Logs the promotion and routes it to SMS, WhatsApp, or Email"""
    if frappe.session.user == "Guest":
        frappe.throw("Unauthorized", frappe.PermissionError)

    # 1. Log the Promo to the Database
    promo = frappe.new_doc("Promotion")
    promo.title = title
    promo.restaurant = restaurant
    promo.channel = channel
    promo.outlet = outlet
    promo.target_audience = target_audience
    promo.message = message
    promo.status = "Sending"
    promo.insert(ignore_permissions=True)
    
    # 2. Filter target customers
    filters = {"custom_restaurant": restaurant}
    if outlet:
        filters["custom_outlet"] = outlet
        
    # Ensure these fields match your database perfectly! 
    # If your phone number field is called something else (like 'phone'), change 'mobile_no' to match it.
    # 🎯 THE FIX: Changed to "phone" and "email"
    all_customers = frappe.get_all("Customer", filters=filters, fields=["name", "phone", "email", "country_code"])
    
    if target_audience == "Specific Customers" and specific_customers:
        selected_ids = json.loads(specific_customers)
        targets = [c for c in all_customers if c.name in selected_ids]
    else:
        targets = all_customers

    if not targets:
        frappe.throw("No customers found for this audience.")

    success_count = 0

    # ==========================================
    # 🟢 EMAIL (Built-in Frappe)
    # ==========================================
    if channel == "Email":
        recipients = [c.email for c in targets if c.email] # 🎯 Changed to c.email
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=title,
                content=message,
                now=True 
            )
            success_count = len(recipients)

    # ==========================================
    # 🔵 SMS & WHATSAPP (Twilio)
    # ==========================================
    elif channel in ["SMS", "WhatsApp"]:
        try:
            from twilio.rest import Client
        except ImportError:
            frappe.throw("Twilio library not installed. Run: env/bin/pip install twilio")

        rest_doc = frappe.get_doc("Restaurant", restaurant)
        sid = rest_doc.twilio_sid
        token = rest_doc.get_password("twilio_auth_token")
        
        if not sid or not token:
            frappe.throw(f"Twilio credentials missing for {restaurant}.")

        client = Client(sid, token)

        for cust in targets:
            if not cust.phone: # 🎯 Changed to cust.phone
                continue
            
            # Format phone number to E.164 standard
            c_code = str(cust.country_code or "").replace("+", "")
            formatted_number = f"+{c_code}{cust.phone}" if c_code else f"+{cust.phone}"
                
            try:
                if channel == "SMS":
                    sender = rest_doc.twilio_sms_number
                    client.messages.create(body=message, from_=sender, to=formatted_number)
                
                elif channel == "WhatsApp":
                    sender = rest_doc.twilio_whatsapp_number
                    client.messages.create(
                        body=message, 
                        from_=f"whatsapp:{sender}", 
                        to=f"whatsapp:{formatted_number}"
                    )
                success_count += 1
            except Exception as e:
                frappe.log_error(f"Twilio {channel} Failed for {formatted_number}", str(e))

    promo.db_set("status", "Completed")
    frappe.db.commit()
    
    return {"success": True, "sent": success_count}