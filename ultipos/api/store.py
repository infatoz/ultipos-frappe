# store.py:
import frappe
from ultipos.api.utils import get_outlet, get_online_store_settings


@frappe.whitelist(allow_guest=True)
def ping():
    return "UltiPOS API working"


# ✅ NEW: return all outlets (store list)
@frappe.whitelist(allow_guest=True)
def get_stores():
    outlets = frappe.get_all(
        "Outlet",
        filters={"disabled": 0} if frappe.db.has_column("Outlet", "disabled") else None,
        fields=[
            "name",
            "outlet_name",
            "outlet_code",
            "address_line_1",
            "suburb",
            "state",
            "phone",
            "email",
            "is_accepting_orders",
            "restaurant",
        ],
        order_by="modified desc",
    )

    stores = []
    for outlet in outlets:
        stores.append({
            "id": outlet.name,
            "name": outlet.outlet_name,
            "outlet_code": outlet.outlet_code,
            "is_open": bool(outlet.is_accepting_orders),
            "address": f"{outlet.address_line_1 or ''}, {outlet.suburb or ''}, {outlet.state or ''}".strip(", "),
            "phone": outlet.phone,
            "email": outlet.email,
            "restaurant_id": outlet.restaurant,
        })

    return {"stores": stores}


@frappe.whitelist(allow_guest=True)
def get_store(outlet_code):
    outlet = get_outlet(outlet_code)

    restaurant = frappe.get_doc("Restaurant", outlet.restaurant)
    store_settings = get_online_store_settings(restaurant.name)

    return {
        "restaurant": {
            "id": restaurant.name,
            "name": getattr(restaurant, "restaurant_name", restaurant.name),
            "logo": getattr(store_settings, "logo", None) if store_settings else None,
            "primary_color": getattr(store_settings, "primary_color", None) if store_settings else None,
            "theme": getattr(store_settings, "theme", None) if store_settings else None,
        },
        "outlet": {
            "id": outlet.name,
            "name": outlet.outlet_name,
            "outlet_code": outlet.outlet_code,
            "is_open": bool(outlet.is_accepting_orders),
            "address": f"{outlet.address_line_1}, {outlet.suburb}, {outlet.state}",
            "phone": outlet.phone,
            "email": outlet.email,
        },
    }


@frappe.whitelist(allow_guest=True)
def get_ordering_config(outlet_code):
    outlet = get_outlet(outlet_code)

    restaurant = frappe.get_doc("Restaurant", outlet.restaurant)
    store_settings = get_online_store_settings(restaurant.name)

    allowed_order_types = []
    payment_methods = []

    if store_settings:
        allowed_order_types = (store_settings.allowed_order_types or "").split("\n")
        payment_methods = (store_settings.payment_methods or "").split("\n")

    return {
        "outlet_code": outlet.outlet_code,
        "allowed_order_types": allowed_order_types or ["Delivery", "Pickup"],
        "payment_methods": payment_methods or ["COD"],
        "tax_percent": 0,
        "delivery_fee": 0,
        "min_order_amount": 0,
    }