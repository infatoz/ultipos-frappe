import frappe
import stripe
from frappe.utils import get_url

@frappe.whitelist(allow_guest=True)
def create_checkout_session(order_id):
    """
    Generates a secure Stripe Checkout URL for the frontend to redirect to.
    """
    if not order_id:
        frappe.throw("Order ID is required")

    order = frappe.get_doc("Order", order_id)
    
    # 1. Find the restaurant this order belongs to
    outlet = frappe.get_doc("Outlet", order.outlet, ignore_permissions=True)
    restaurant = outlet.restaurant

    # 2. Fetch the Stripe Settings Name
    settings_name = frappe.db.get_value(
        "Stripe Settings",
        {"restaurant": restaurant, "is_enabled": 1},
        "name"
    )

    if not settings_name:
        frappe.throw(f"Stripe is not configured or enabled for {restaurant}.")

    # 🎯 THE SECURITY FIX: Load the full document and DECRYPT the password
    settings_doc = frappe.get_doc("Stripe Settings", settings_name)
    actual_secret_key = settings_doc.get_password("secret_key")

    # 3. Authenticate with Stripe
    stripe.api_key = actual_secret_key

    try:
        # 4. Create the Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aud', 
                    'product_data': {
                        'name': f"Order {order.name} - {restaurant}",
                        'description': f"Pickup/Delivery from {outlet.outlet_name or outlet.name}"
                    },
                    'unit_amount': int(order.total_amount * 100), 
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"http://localhost:5173/order-status/{order.name}?payment=success",
            cancel_url=f"http://localhost:5173/order-status/{order.name}?payment=cancelled",
            metadata={
                "order_id": order.name 
            }
        )

        return {
            "success": True,
            "redirect_url": session.url
        }

    except Exception as e:
        # 🎯 THE LOGGER FIX: Explicitly assign title and message so it doesn't break the 140 char limit
        frappe.log_error(title="Stripe Checkout Failed", message=str(e))
        frappe.throw("Could not connect to payment gateway. Please try again.")

@frappe.whitelist(allow_guest=True)
def webhook():
    # Read the raw JSON directly to avoid Stripe library key crashes
    payload = frappe.request.get_json()

    # We only care about the checkout success event
    if payload.get("type") == 'checkout.session.completed':
        session = payload.get("data", {}).get("object", {})
        order_id = session.get("metadata", {}).get("order_id")

        if order_id:
            try:
                # 1. Fetch the Order
                order = frappe.get_doc("Order", order_id)
                order.db_set("payment_status", "Paid")
                
                # 2. 🎯 THE GHOST SLAYER: Check the Auto-Accept toggle (Bypassing cache!)
                auto_accept_val = frappe.db.get_value("Outlet", order.outlet, "auto_accept_orders")
                
                if int(auto_accept_val or 0) == 1:
                    order.db_set("order_status", "Accepted") # Auto-route to Kitchen
                else:
                    order.db_set("order_status", "New") # Send to FOH Dashboard to ring the bell!
                
                # 3. Create the official payment receipt
                if not frappe.db.exists("Order Payment", {"order": order_id}):
                    payment_doc = frappe.new_doc("Order Payment")
                    payment_doc.order = order_id
                    payment_doc.amount = order.total_amount
                    payment_doc.payment_method = "Online" 
                    payment_doc.platform = "Web"
                    
                    # 4. 🎯 THE TYPO FIX: Match your database's exact spelling!
                    payment_doc.status = "Sucess" 
                    payment_doc.transaction_id = session.get("payment_intent")
                    
                    payment_doc.insert(ignore_permissions=True)
                
                frappe.db.commit()

            except Exception as e:
                # If Frappe crashes again, it will log the EXACT reason in the Error Log!
                frappe.log_error(title="Webhook DB Crash", message=str(e) + "\n" + frappe.get_traceback())
                return "Crash", 500

    return "OK", 200