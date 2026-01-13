# import frappe
# from ultipos.api.utils import _loads, get_outlet, get_worldline_settings
# from ultipos.api.worldline import worldline_create_payment


# @frappe.whitelist(allow_guest=True)
# def create_intent(outlet_code, amount, customer, order_id=None):
#     outlet = get_outlet(outlet_code)

#     customer = _loads(customer) or {}
#     if not isinstance(customer, dict):
#         frappe.throw("Invalid customer payload")

#     amount = float(amount or 0)

#     # ✅ DEV MODE: redirect to YOUR frontend payment page
#     if frappe.conf.get("developer_mode") == 1:
#         return {
#             "payment_gateway": "Worldline",
#             "redirect_url": f"http://localhost:5173/worldline-pay?amount={amount}&order_id=",
#             "mock": True
#         }


#     # ✅ REAL MODE: use Worldline API
#     restaurant = frappe.get_doc("Restaurant", outlet.restaurant)
#     settings = get_worldline_settings(restaurant.name)

#     redirect_url = worldline_create_payment(settings, amount, customer)

#     return {
#         "payment_gateway": "Worldline",
#         "redirect_url": redirect_url,
#         "mock": False
#     }
    
import frappe
from ultipos.api.utils import _loads, get_outlet, get_worldline_settings
from ultipos.api.worldline import worldline_create_payment


@frappe.whitelist(allow_guest=True)
def create_intent(outlet_code, amount, customer, order_id):
    outlet = get_outlet(outlet_code)
    customer = _loads(customer)

    if not isinstance(customer, dict):
        frappe.throw("Invalid customer")

    amount = int(float(amount))

    # 🔹 DEV MODE
    if frappe.conf.get("developer_mode"):
        return {
            "redirect_url":
                f"http://localhost:5173/worldline-pay"
                f"?order_id={order_id}&amount={amount}"
        }

    restaurant = frappe.get_doc("Restaurant", outlet.restaurant)
    settings = get_worldline_settings(restaurant.name)

    redirect_url = worldline_create_payment(
        settings=settings,
        amount=amount,
        customer=customer,
        order_id=order_id
    )

    return {"redirect_url": redirect_url}


# @frappe.whitelist(allow_guest=True)
# def create_intent(outlet_code, amount, customer, order_id=None):
#     outlet = get_outlet(outlet_code)

#     customer = _loads(customer) or {}
#     if not isinstance(customer, dict):
#         frappe.throw("Invalid customer payload")

#     amount = float(amount or 0)

#     # ✅ FIXED DEV MODE CHECK
#     if frappe.conf.get("developer_mode"):
#         return {
#             "payment_gateway": "Worldline",
#             "redirect_url": f"http://localhost:5173/worldline-pay?amount={amount}&order_id={order_id or ''}",
#             "mock": True
#         }

#     # ✅ REAL MODE
#     restaurant = frappe.get_doc("Restaurant", outlet.restaurant)
#     settings = get_worldline_settings(restaurant.name)

#     redirect_url = worldline_create_payment(settings, amount, customer)

#     return {
#         "payment_gateway": "Worldline",
#         "redirect_url": redirect_url,
#         "mock": False
#     }
