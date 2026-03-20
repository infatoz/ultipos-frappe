import frappe
import json

@frappe.whitelist()
def get_campaign_data():
    """Smartly fetches outlets and customers regardless of exact schema names"""
    if frappe.session.user == "Guest":
        frappe.throw("Not logged in", frappe.PermissionError)

    # 1. Find the Restaurant
    restaurant = frappe.db.get_value("Restaurant", {"owner_user": frappe.session.user}, "name")
    if not restaurant:
        return {"success": False, "message": "No restaurant assigned to this user."}

    # 2. Safely Fetch Outlets
    meta_outlet = frappe.get_meta("Outlet")
    out_fields = ["name"]
    if meta_outlet.has_field("outlet_name"): out_fields.append("outlet_name")
    
    out_filters = {}
    if meta_outlet.has_field("restaurant"): out_filters["restaurant"] = restaurant

    outlets = frappe.get_all("Outlet", filters=out_filters, fields=out_fields, ignore_permissions=True)
    for o in outlets:
        # Standardize the output for Javascript
        o["safe_name"] = o.get("outlet_name") or o.name

    # 3. Safely Fetch Customers
    meta_cust = frappe.get_meta("Customer")
    cust_fields = ["name"]
    
    # Grab whatever contact fields actually exist in your database
    for f in ["customer_name", "phone", "mobile_no", "whatsapp", "email"]:
        if meta_cust.has_field(f): cust_fields.append(f)

    cust_filters = {}
    if meta_cust.has_field("custom_restaurant"): cust_filters["custom_restaurant"] = restaurant
    elif meta_cust.has_field("restaurant"): cust_filters["restaurant"] = restaurant

    customers = frappe.get_all("Customer", filters=cust_filters, fields=cust_fields, ignore_permissions=True)
    for c in customers:
        # Standardize the output for Javascript
        c["safe_name"] = c.get("customer_name") or c.name
        c["safe_phone"] = c.get("phone") or c.get("mobile_no") or c.get("whatsapp") or "No Number"

    return {
        "success": True, 
        "restaurant": restaurant, 
        "outlets": outlets, 
        "customers": customers
    }

@frappe.whitelist()
def dispatch_campaign(title, channel, target_audience, message, restaurant, outlet=None, specific_customers=None):
    """Smartly sends the campaign based on available database fields"""
    if frappe.session.user == "Guest":
        frappe.throw("Unauthorized", frappe.PermissionError)

    promo = frappe.new_doc("Promotion")
    promo.title = title
    promo.restaurant = restaurant
    promo.channel = channel
    promo.outlet = outlet
    promo.target_audience = target_audience
    promo.message = message
    promo.status = "Sending"
    promo.insert(ignore_permissions=True)
    
    # Safely determine which fields to fetch
    meta_cust = frappe.get_meta("Customer")
    cust_fields = ["name"]
    for f in ["phone", "mobile_no", "whatsapp", "email", "email_id", "country_code"]:
        if meta_cust.has_field(f): cust_fields.append(f)

    cust_filters = {}
    if meta_cust.has_field("custom_restaurant"): cust_filters["custom_restaurant"] = restaurant
    elif meta_cust.has_field("restaurant"): cust_filters["restaurant"] = restaurant
    if outlet and meta_cust.has_field("custom_outlet"): cust_filters["custom_outlet"] = outlet
        
    all_customers = frappe.get_all("Customer", filters=cust_filters, fields=cust_fields, ignore_permissions=True)
    
    if target_audience == "Specific Customers" and specific_customers:
        selected_ids = json.loads(specific_customers)
        targets = [c for c in all_customers if c.name in selected_ids]
    else:
        targets = all_customers

    if not targets:
        frappe.throw("No customers found for this audience.")

    success_count = 0

    # ==========================================
    # 🟢 EMAIL
    # ==========================================
    if channel == "Email":
        recipients = [c.get("email") or c.get("email_id") for c in targets if c.get("email") or c.get("email_id")]
        if recipients:
            frappe.sendmail(recipients=recipients, subject=title, content=message, now=True)
            success_count = len(recipients)

    # ==========================================
    # 🔵 SMS & WHATSAPP
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
            # Smartly grab whatever phone field is available
            phone_val = cust.get("phone") or cust.get("mobile_no") or cust.get("whatsapp")
            if not phone_val:
                continue
            
            c_code = str(cust.get("country_code") or "").replace("+", "")
            formatted_number = f"+{c_code}{phone_val}" if c_code else f"+{phone_val}"
                
            try:
                if channel == "SMS":
                    sender = rest_doc.twilio_sms_number
                    client.messages.create(body=message, from_=sender, to=formatted_number)
                elif channel == "WhatsApp":
                    sender = rest_doc.twilio_whatsapp_number
                    client.messages.create(body=message, from_=f"whatsapp:{sender}", to=f"whatsapp:{formatted_number}")
                success_count += 1
            except Exception as e:
                frappe.log_error(f"Twilio {channel} Failed for {formatted_number}", str(e))

    promo.db_set("status", "Completed")
    frappe.db.commit()
    return {"success": True, "sent": success_count}