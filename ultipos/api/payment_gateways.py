import frappe
import stripe
import json
import requests
import hmac
import hashlib
import base64
from email.utils import formatdate
from worldline.connect.sdk.factory import Factory
from worldline.connect.sdk.communicator_configuration import CommunicatorConfiguration
from worldline.connect.sdk.v1.domain.create_hosted_checkout_request import CreateHostedCheckoutRequest
from worldline.connect.sdk.v1.domain.hosted_checkout_specific_input import HostedCheckoutSpecificInput
from worldline.connect.sdk.v1.domain.amount_of_money import AmountOfMoney
from worldline.connect.sdk.v1.domain.order import Order
from worldline.connect.sdk.v1.domain.customer import Customer

@frappe.whitelist(allow_guest=True)
def get_active_gateways(outlet_code=None):
    """Tells the React frontend which payment buttons to render"""
    
    # 🎯 Bulletproof Extraction
    if not outlet_code:
        outlet_code = frappe.form_dict.get("outlet_code")
        
    if not outlet_code:
        return []

    outlet_name = frappe.db.get_value("Outlet", {"outlet_code": outlet_code}, "name")
    if not outlet_name: return []
    outlet = frappe.get_doc("Outlet", outlet_name, ignore_permissions=True)

    settings = frappe.db.get_value(
        "Payment Gateway Settings",
        {"restaurant": outlet.restaurant, "is_enabled": 1},
        ["enable_stripe", "enable_worldline", "enable_tyro"],
        as_dict=True
    )

    gateways = []
    if settings:
        if settings.enable_stripe: gateways.append("Stripe")
        if settings.enable_worldline: gateways.append("Worldline")
        if settings.enable_tyro: gateways.append("Tyro")

    return gateways


@frappe.whitelist(allow_guest=True)
def create_checkout_session(order_id=None, gateway=None):
    """The Universal Payment Router!"""
    
    # 🎯 BULLETPROOF EXTRACTION: Catch variables no matter how React formats them!
    if not order_id:
        order_id = frappe.form_dict.get("order_id")
    if not gateway:
        gateway = frappe.form_dict.get("gateway") or "Stripe"

    # Deep check the raw JSON body just in case
    if not order_id:
        try:
            payload = frappe.request.get_json()
            if payload:
                order_id = payload.get("order_id")
                gateway = payload.get("gateway", gateway)
        except Exception:
            pass

    if not order_id:
        frappe.throw("Order ID is required")

    order = frappe.get_doc("Order", order_id)
    outlet = frappe.get_doc("Outlet", order.outlet, ignore_permissions=True)
    restaurant = outlet.restaurant

    settings_name = frappe.db.get_value(
        "Payment Gateway Settings",
        {"restaurant": restaurant, "is_enabled": 1},
        "name"
    )

    if not settings_name:
        frappe.throw(f"No active payment configuration found for {restaurant}.")

    settings_doc = frappe.get_doc("Payment Gateway Settings", settings_name)

    # ==========================================
    # 🟠 STRIPE ROUTING
    # ==========================================
    if gateway == "Stripe":
        if not settings_doc.enable_stripe:
            frappe.throw("Stripe is not currently enabled.")
            
        stripe.api_key = settings_doc.get_password("stripe_secret_key")

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'aud', 
                        'product_data': {
                            'name': f"Order {order.order_number}",
                            'description': f"From {outlet.outlet_name or outlet.name}"
                        },
                        'unit_amount': int(order.total_amount * 100), 
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"http://localhost:5173/order-status/{order.name}?payment=success",
                cancel_url=f"http://localhost:5173/order-status/{order.name}?payment=cancelled",
                metadata={"order_id": order.name}
            )
            return {"success": True, "gateway": "Stripe", "redirect_url": session.url}

        except Exception as e:
            frappe.log_error(title="Stripe Failed", message=str(e))
            frappe.throw("Stripe gateway error. Please try again.")

#     # ==========================================
#     # 🔵 REAL WORLDLINE ROUTING (Official SDK)
#     # ==========================================

      # ==========================================
    # 🔵 WORLDLINE & 🟢 TYRO ROUTING (Demo Mock Mode)
    # ==========================================
    elif gateway in ["Worldline", "Tyro"]:
        # Check if they are enabled in Frappe Desk
        if gateway == "Worldline" and not settings_doc.enable_worldline:
            frappe.throw("Worldline is not currently enabled.")
        if gateway == "Tyro" and not settings_doc.enable_tyro:
            frappe.throw("Tyro is not currently enabled.")

        # 🎯 Send them straight to your React Mock Screen!
        redirect_url = f"http://localhost:5173/fake-payment?order_id={order.name}&amount={order.total_amount}&gateway={gateway}"
        
        return {
            "success": True, 
            "gateway": gateway, 
            "redirect_url": redirect_url
        }

    else:
        frappe.throw("Invalid Payment Gateway selected.")
#     elif gateway == "Worldline":
#         if not settings_doc.enable_worldline:
#             frappe.throw("Worldline is not currently enabled.")

#         # 1. Grab the NUMERIC Merchant ID
#         merchant_id = str(settings_doc.worldline_merchant_id).strip()
#         full_api_key = settings_doc.get_password("worldline_api_key")

#         if not full_api_key or ":" not in full_api_key:
#             frappe.throw("Worldline API Key format invalid. Must be API_KEY_ID:SECRET_KEY")

#         api_key_id, secret_api_key = full_api_key.split(":", 1)

#         merchant_customer_id = "Guest"
#         if order.get("order_customer") and len(order.order_customer) > 0:
#             merchant_customer_id = str(order.order_customer[0].customer)

#         # 2. Setup Worldline SDK Configuration
#         config = CommunicatorConfiguration(
#             api_key_id=api_key_id.strip(),
#             secret_api_key=secret_api_key.strip(),
#             # 🎯 SDK strictly requires NO https:// here!
#             api_endpoint="api.preprod.connect.worldline-solutions.com", 
#             integrator="UltiPOS"
#         )
        
#         config.connect_timeout = 20
#         config.socket_timeout = 20
#         config.authorization_type = "v1HMAC" 
#         config.max_connections = 10 
        
#         try:
#             # 3. Open a secure connection
#             with Factory.create_client_from_configuration(config) as client:
                
#                 amount_of_money = AmountOfMoney()
#                 amount_of_money.amount = int(order.total_amount * 100)
#                 amount_of_money.currency_code = "AUD"

#                 customer = Customer()
#                 customer.merchant_customer_id = merchant_customer_id

#                 worldline_order = Order()
#                 worldline_order.amount_of_money = amount_of_money
#                 worldline_order.customer = customer

#                 hosted_checkout_input = HostedCheckoutSpecificInput()
#                 hosted_checkout_input.return_url = f"http://localhost:5173/order-status/{order.name}?payment=return"

#                 request = CreateHostedCheckoutRequest()
#                 request.order = worldline_order
#                 request.hosted_checkout_specific_input = hosted_checkout_input

#                 # 4. Send to Worldline!
#                 response = client.v1().merchant(merchant_id).hostedcheckouts().create(request)
                
#                 # Extract URL and format it
#                 partial_url = response.partial_redirect_url
#                 if partial_url.startswith("http"):
#                     redirect_url = partial_url
#                 elif partial_url.startswith("/"):
#                     redirect_url = "https://payment.preprod.connect.worldline-solutions.com" + partial_url
#                 else:
#                     redirect_url = "https://" + partial_url
                
#                 return {"success": True, "gateway": "Worldline", "redirect_url": redirect_url}

#         except Exception as e:
#             frappe.log_error("Worldline SDK Error", str(e))
#             frappe.throw(f"Worldline SDK Failed. Check Error Logs.")

#     # ==========================================
#     # 🟢 TYRO ROUTING (MOCK TEST MODE)
#     # ==========================================

#     else:
#         frappe.throw("Invalid Payment Gateway selected.")

# @frappe.whitelist(allow_guest=True)
# def process_mock_payment(order_id, gateway):
#     """React calls this when you click YES PAY on the FakePayment screen"""
#     if not order_id:
#         return {"success": False}
        
#     order = frappe.get_doc("Order", order_id)

#     order.db_set("payment_status", "Paid")
#     auto_accept = int(frappe.db.get_value("Outlet", order.outlet, "auto_accept_orders") or 0)
#     order.db_set("order_status", "Accepted" if auto_accept else "New") 

#     if not frappe.db.exists("Order Payment", {"order": order.name}):
#         payment_doc = frappe.new_doc("Order Payment")
#         payment_doc.order = order.name
#         payment_doc.amount = order.total_amount
#         payment_doc.payment_method = "Online" 
#         payment_doc.platform = "Web"
#         payment_doc.status = "Sucess" # 🎯 Kept the typo fix!
#         payment_doc.transaction_id = f"MOCK_{gateway.upper()}_TX"
#         payment_doc.insert(ignore_permissions=True)

#     frappe.db.commit()
#     return {"success": True}


@frappe.whitelist(allow_guest=True)
def stripe_webhook():
    payload = frappe.request.get_json()

    if payload.get("type") == 'checkout.session.completed':
        session = payload.get("data", {}).get("object", {})
        order_id = session.get("metadata", {}).get("order_id")

        if order_id:
            try:
                order = frappe.get_doc("Order", order_id)
                order.db_set("payment_status", "Paid")
                
                auto_accept = int(frappe.db.get_value("Outlet", order.outlet, "auto_accept_orders") or 0)
                order.db_set("order_status", "Accepted" if auto_accept else "New") 
                
                if not frappe.db.exists("Order Payment", {"order": order_id}):
                    payment_doc = frappe.new_doc("Order Payment")
                    payment_doc.order = order_id
                    payment_doc.amount = order.total_amount
                    payment_doc.payment_method = "Online" 
                    payment_doc.platform = "Web"
                    payment_doc.status = "Sucess" # 🎯 Typo fixed here!
                    payment_doc.transaction_id = session.get("payment_intent")
                    payment_doc.insert(ignore_permissions=True)
                
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(title="Webhook Crash", message=str(e))
                return "Crash", 500

    return "OK", 200