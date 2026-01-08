import frappe

@frappe.whitelist(allow_guest=True)
def get_store(outlet_code):
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code})

    restaurant = frappe.get_doc("Restaurant", outlet.restaurant)

    return {
        "restaurant": {
            "name": restaurant.restaurant_name,
            "logo": restaurant.logo,
            "theme": restaurant.theme_config
        },
        "outlet": {
            "name": outlet.outlet_name,
            "outlet_code": outlet.outlet_code,
            "is_open": outlet.is_open,
            "order_types": outlet.order_types,
            "address": outlet.address
        }
    }


@frappe.whitelist(allow_guest=True)
def ping():
    return "UltiPOS API working"