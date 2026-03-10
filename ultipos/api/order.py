import frappe
import json
from frappe.model.naming import make_autoname
from frappe.utils import now
from ultipos.api.coupon import validate_coupon


@frappe.whitelist(allow_guest=True)
def place(order_data):
    if isinstance(order_data, str):
        order_data = json.loads(order_data)

    outlet_code = order_data.get("outlet_code")
    customer_id = order_data.get("customer_id")
    items = order_data.get("items")

    if not outlet_code: frappe.throw("outlet_code is required")
    if not customer_id: frappe.throw("customer_id is required")
    if not items: frappe.throw("Items required")

    if isinstance(items, str):
        items = json.loads(items)

    # ----------------------------
    # 1. Extract Payment Method FIRST
    # ----------------------------
    payment_info = order_data.get("payment", {})
    if isinstance(payment_info, str):
        payment_info = json.loads(payment_info)
    pay_method = payment_info.get("method")

    # ----------------------------
    # 2. Fetch Outlet + Enforce Toggles
    # ----------------------------
    outlet = frappe.get_doc("Outlet", {"outlet_code": outlet_code}, ignore_permissions=True)
    if not outlet:
        frappe.throw(f"Outlet {outlet_code} not found")

    # 🎯 THE FIX: Use the actual field name "is_accepting_orders"
    if not outlet.is_accepting_orders:
        frappe.throw("Sorry, this store is currently not accepting new orders.")

    # ----------------------------
    # 3. Create Order
    # ----------------------------
    order = frappe.new_doc("Order")
    order.flags.ignore_permissions = True
    order.order_number = make_autoname("ORD-.YYYY.-.#####")
    order.restaurant = outlet.restaurant
    order.outlet = outlet.name
    order.platform = order_data.get("platform", "Web")
    order.order_type = order_data.get("order_type", "Delivery")
    
    # 🎯 THE FIX: Clean Auto-Accept Logic
    # ----------------------------
    # 🎯 THE FIX: Hold Stripe orders in the "Ghost" zone until paid!
    # ----------------------------
    if pay_method == "COD":
        # COD goes straight to the FOH (or Kitchen if Auto-Accept is on)
        if outlet.auto_accept_orders:
            order.order_status = "Accepted"
        else:
            order.order_status = "New"
    else:
        # STRIPE ONLINE PAYMENT -> Hide it from the staff!
        order.order_status = "Awaiting Payment"

    order.payment_status = "Awaiting"
    order.order_time = now()
    order.notes = order_data.get("notes")

    total_amount = 0

    # ----------------------------
    # Order Items (Keep your existing items loop here)
    # ----------------------------

    # ----------------------------
    # Order Items
    # ----------------------------
    for it in items:
        row = order.append("order_item", {})
        row.menu_item = it.get("menu_item")
        row.item_name = it.get("item_name")
        
        # 🎯 Set KDS Status and catch the customer's Item Note!
        row.item_status = "Received"
        row.notes = it.get("note") 
        
        parent_qty = int(it.get("qty", 1))
        row.qty = parent_qty
        row.show_in_kds = it.get("show_in_kds", 1)
        
        mods = it.get("modifiers", [])
        
        # 1. Figure out how much of the unit price is just from modifiers
        mod_cost_per_item = sum(float(m.get("price", 0)) for m in mods)
        
        # 2. Subtract the modifiers to get the TRUE base price
        bundled_unit_price = float(it.get("unit_price", 0))
        row.unit_price = bundled_unit_price - mod_cost_per_item
        
        # The line total remains the same
        row.total_price = float(it.get("total_price", 0))
        
        # 3. Save the Modifiers
        if mods:
            row.modifiers = json.dumps(mods)
            
            for m in mods:
                mod_row = order.append("order_item_modifier", {})
                mod_row.modifier_name = m.get("name")
                mod_row.price = float(m.get("price", 0))
                
                # Make sure if they order 2 items, the kitchen knows to make 2 modifiers!
                m_qty = int(m.get("qty", 1))
                mod_row.qty = m_qty * parent_qty
                
                mod_row.item_name = it.get("item_name")

        total_amount += row.total_price

    # ----------------------------
    # 🎯 NEW: Coupon & Discount Logic
    # ----------------------------
    subtotal = total_amount
    discount_amount = 0
    coupon_code = order_data.get("coupon_code")

    if coupon_code:
        try:
            # Run your coupon.py logic securely on the backend
            coupon_res = validate_coupon(outlet_code, coupon_code, subtotal)
            if coupon_res and coupon_res.get("valid"):
                discount_amount = coupon_res.get("discount", 0)
                
                # Save the actual text code to the database if the field exists
                order.coupon_code = coupon_code 
        except Exception as e:
            # If the coupon is invalid/expired, we log it but don't crash the order
            frappe.log_error(f"Coupon failed: {str(e)}", "Coupon Error")
            pass

    # Lock in the final math
    order.discount_amount = discount_amount
    order.total_amount = subtotal - discount_amount

    # ----------------------------
    # Order Customer (Child Table)
    # ----------------------------
    order.append("order_customer", {
        "customer": customer_id,
        "name1": order_data.get("customer_name"),
        "phone": order_data.get("customer_phone"),
        "email": order_data.get("customer_email"),
        "delivery_address": order_data.get("delivery_address")
    })

    # ----------------------------
    # Save
    # ----------------------------
    order.insert()
    frappe.db.commit()

    return {
        "order_id": order.name,
        "status": order.order_status,
        "amount": order.total_amount
    }

# def place(order_data):
#     # --------------------
#     # Parse payload
#     # --------------------
#     if isinstance(order_data, str):
#         order_data = frappe.parse_json(order_data)

#     items = order_data.get("items")
#     outlet_code = order_data.get("outlet_code")
#     customer_id = order_data.get("customer_id")

#     if not items:
#         frappe.throw("Items required")

#     if not outlet_code:
#         frappe.throw("outlet_code required")

#     # ✅ IMPORTANT: outlet_code is NOT the document name
#     outlet_name = frappe.db.get_value(
#         "Outlet",
#         {"outlet_code": outlet_code},
#         "name"
#     )

#     if not outlet_name:
#         frappe.throw(f"Outlet {outlet_code} not found")


#     outlet = frappe.get_doc("Outlet", outlet_name, ignore_permissions=True)

#     if not outlet.restaurant:
#         frappe.throw("Outlet has no linked restaurant")

#     # --------------------
#     # Create Order
#     # --------------------
#     order = frappe.new_doc("Order")
#     order.flags.ignore_permissions = True
#     order.order_number = make_autoname("ORD-.YYYY.-.#####")
#     order.restaurant = outlet.restaurant      # ✅ MANDATORY
#     order.outlet = outlet_name          # ✅ DOC NAME
#     order.customer = customer_id
#     order.platform = order_data.get("platform", "Web")
#     order.order_type = order_data.get("order_type", "Delivery")
#     order.order_status = "New"
#     order.payment_status = "Awaiting"
#     order.posting_date = now()

#     total_amount = 0

#     # --------------------
#     # Order Items (FIXED)
#     # --------------------
#     for it in items:
#         row = order.append("order_item", {})  # ✅ CORRECT CHILD TABLE
#         row.menu_item = it.get("menu_item")
#         row.item_name = it.get("item_name")
#         row.qty = it.get("qty", 1)
#         row.unit_price = it.get("unit_price", 0)
#         row.total_price = it.get("total_price", 0)

#         total_amount += row.total_price

#     order.total_amount = total_amount

#     order.insert()
#     frappe.db.commit()

#     return {
#         "order_id": order.name,
#         "status": order.order_status,
#         "amount": order.total_amount
#     }

# @frappe.whitelist(allow_guest=True)
# def place(order_data):
#     if isinstance(order_data, str):
#         order_data = frappe.parse_json(order_data)

#     items = order_data.get("items")

#     # ✅ FIX: parse string → list
#     if isinstance(items, str):
#         items = frappe.parse_json(items)

#     if not items or not isinstance(items, list):
#         frappe.throw("Items must be a list")

#     outlet_code = order_data.get("outlet_code")
#     if not outlet_code:
#         frappe.throw("outlet_code is required")

#     # ⚠️ IMPORTANT: check by outlet_code field, NOT name
#     outlet_name = frappe.db.get_value(
#         "Outlet",
#         {"outlet_code": outlet_code},
#         "name"
#     )
#     if not outlet_name:
#         frappe.throw(f"Outlet {outlet_code} not found")

#     order = frappe.new_doc("Order")
#     order.flags.ignore_permissions = True
#     order.outlet = outlet_name
#     order.customer = order_data.get("customer_id")
#     order.status = "AWAITING_PAYMENT"
#     order.platform = order_data.get("platform", "Web")
#     order.order_type = order_data.get("order_type", "Delivery")

#     total_amount = 0

#     for it in items:
#         row = order.append("items", {})
#         row.menu_item = it["menu_item"]
#         row.item_name = it["item_name"]
#         row.qty = it["qty"]
#         row.unit_price = it["unit_price"]
#         row.total_price = it["total_price"]
#         total_amount += row.total_price

#     order.total_amount = total_amount
#     order.insert()
#     frappe.db.commit()

#     return {
#         "order_id": order.name,
#         "status": order.status,
#         "amount": total_amount
#     }


# def place(order_data):
#     if isinstance(order_data, str):
#         order_data = frappe.parse_json(order_data)

#     if not order_data.get("items"):
#         frappe.throw("Items required")

#     outlet_code = order_data.get("outlet_code")

#     outlet_name = frappe.db.get_value(
#         "Outlet",
#         {"outlet_code": outlet_code},
#         "name"
#     )

#     if not outlet_name:
#         frappe.throw(f"Outlet with code {outlet_code} not found")

#     order = frappe.new_doc("Order")
#     order.outlet_code = outlet_code
#     order.customer = order_data.get("customer_id")
#     order.status = "AWAITING_PAYMENT"
#     order.platform = order_data.get("platform", "Web")
#     order.order_type = order_data.get("order_type", "Delivery")
#     order.posting_date = frappe.utils.now()

#     for it in order_data["items"]:
#         order.append("items", {
#             "menu_item": it["menu_item"],
#             "item_name": it["item_name"],
#             "qty": it["qty"],
#             "unit_price": it["unit_price"],
#             "total_price": it["total_price"]
#         })

#     order.insert(ignore_permissions=True)

#     return {
#         "order_id": order.name,
#         "status": order.status,
#         "amount": sum(i.total_price for i in order.items)
#     }


# @frappe.whitelist(allow_guest=True)
# def place(order_data):
#     if isinstance(order_data, str):
#         order_data = frappe.parse_json(order_data)

#     if not order_data.get("items"):
#         frappe.throw("Items required")

#     outlet_code = order_data.get("outlet_code")
#     if not frappe.db.exists("Outlet", outlet_code):
#         frappe.throw(f"Outlet {outlet_code} not found")

#     order = frappe.new_doc("Order")
#     order.outlet_code = outlet_code
#     order.customer = order_data.get("customer_id")
#     order.status = "AWAITING_PAYMENT"
#     order.platform = order_data.get("platform", "Web")
#     order.order_type = order_data.get("order_type", "Delivery")
#     order.posting_date = now()

#     for it in order_data["items"]:
#         order.append("items", {
#             "menu_item": it["menu_item"],
#             "item_name": it["item_name"],
#             "qty": it["qty"],
#             "unit_price": it["unit_price"],
#             "total_price": it["total_price"]
#         })

#     order.insert(ignore_permissions=True)

#     return {
#         "order_id": order.name,
#         "status": order.status,
#         "amount": sum(i.total_price for i in order.items)
#     }

# @frappe.whitelist(allow_guest=True)
# def place(order_data=None):
#     """
#     Public API to place an order (Web / Kiosk / Aggregators)
#     """

#     if not order_data:
#         frappe.throw("order_data is required")

#     # --------------------
#     # Parse order_data safely
#     # --------------------
#     try:
#         if isinstance(order_data, str):
#             order_data = json.loads(order_data)
#     except Exception:
#         frappe.throw("Invalid order_data JSON")

#     outlet_code = order_data.get("outlet_code")
#     customer_id = order_data.get("customer_id")
#     items = order_data.get("items")
#     payment = order_data.get("payment")
#     coupon_code = order_data.get("coupon_code")
#     order_type = order_data.get("order_type") or "Delivery"
#     platform = order_data.get("platform") or "Web"
#     notes = order_data.get("notes")

    


#     # --------------------
#     # Validations
#     # --------------------
#     if not outlet_code:
#         frappe.throw("outlet_code is required")

#     if not customer_id:
#         frappe.throw("customer_id is required")

#     if not items or not isinstance(items, list):
#         frappe.throw("items must be a list")

#     if not payment or not isinstance(payment, dict):
#         frappe.throw("payment is required")

#     # --------------------
#     # Fetch Outlet (Guest-safe)
#     # --------------------
#     # outlet = frappe.get_doc("Outlet", outlet_code, ignore_permissions=True)
#     outlet_name = frappe.db.get_value(
#     "Outlet",
#     {"outlet_code": outlet_code},
#     "name"
#     )

#     if not outlet_name:
#         frappe.throw(f"Outlet with code {outlet_code} not found")

#     outlet = frappe.get_doc("Outlet", outlet_name, ignore_permissions=True)
#     restaurant = outlet.restaurant

#     # --------------------
#     # Create Order
#     # --------------------
#     order = frappe.new_doc("Order")
#     order.flags.ignore_permissions = True

#     order.order_number = make_autoname("ORD-.YYYY.-.#####")
#     order.restaurant = restaurant
#     order.outlet = outlet.name
#     order.platform = "Web"
#     order.order_type = order_type
#     order.order_status = "New"
#     order.payment_status = "Awaiting"
#     order.notes = notes


#     # --------------------
#     # Order Items
#     # --------------------
#     total_amount = 0

#     for i in items:
#         row = order.append("order_item", {})
#         row.menu_item = i.get("menu_item")
#         row.item_name = i.get("item_name")
#         row.qty = i.get("qty", 1)
#         row.unit_price = i.get("unit_price", 0)
#         row.total_price = i.get("total_price", 0)

#         total_amount += row.total_price

#     order.total_amount = total_amount

#     # --------------------
#     # Save
#     # --------------------
#     order.insert()
#     frappe.db.commit()

#     return {
#         "status": "success",
#         "order_id": order.name,
#         "total": order.total_amount
#     }

@frappe.whitelist(allow_guest=True)
def create_draft(order_data):
    if isinstance(order_data, str):
        order_data = frappe.parse_json(order_data)

    outlet_code = order_data.get("outlet_code")
    customer = order_data.get("customer")
    items = order_data.get("items")
    amounts = order_data.get("amounts")

    if not outlet_code or not items:
        frappe.throw("Invalid order data")

    # 🔹 Resolve outlet → restaurant
    outlet = frappe.get_doc(
        "Outlet",
        {"outlet_code": outlet_code},
        ignore_permissions=True
    )

    order = frappe.new_doc("Order")
    order.flags.ignore_permissions = True

    order.restaurant = outlet.restaurant
    order.outlet = outlet.name
    order.platform = "Web"
    order.order_type = order_data.get("order_type", "Delivery")
    order.order_status = "New"
    order.payment_status = "Awaiting"
    order.total_amount = amounts["total"]
    order.tax_amount = amounts.get("tax", 0)
    order.discount_amount = amounts.get("discount", 0)
    order.order_time = now()

    # 👤 customer (child table)
    order.append("order_customer", {
        "name1": customer["name"],
        "phone": customer["phone"],
        "email": customer.get("email"),
        "delivery_address": customer.get("address")
    })

    # 🍔 items (NO UNIQUE CONSTRAINT ISSUES)
    for it in items:
        order.append("order_item", {
            "menu_item": it["menu_item"],
            "item_name": it["item_name"],
            "qty": it["qty"],
            "unit_price": it["unit_price"],
            "total_price": it["total_price"]
        })

    order.insert()
    frappe.db.commit()

    return {
        "order_id": order.name,
        "amount": order.total_amount
    }


@frappe.whitelist(allow_guest=True)
def get_status(order_id: str):
    if not order_id:
        frappe.throw("order_id is required")

    # Fetch order (ignore permissions for public tracking)
    order = frappe.get_doc("Order", order_id, ignore_permissions=True)

    # ---------------------------
    # Customer (from child table)
    # ---------------------------
    customer = {}
    if order.order_customer:
        c = order.order_customer[0]
        customer = {
            "name": c.name1,
            "phone": c.phone,
            "email": c.email,
            "address": c.delivery_address
        }

    # ---------------------------
    # Items
    # ---------------------------
    # ---------------------------
    # Items
    # ---------------------------
    items = []
    for it in order.order_item:
        # 🎯 NEW: Parse the string back into a list
        parsed_mods = []
        if getattr(it, "modifiers", None):
            try:
                parsed_mods = json.loads(it.modifiers)
            except Exception:
                pass

        items.append({
            "menu_item": it.menu_item,
            "item_name": it.item_name,
            "qty": it.qty,
            "unit_price": it.unit_price,
            "total_price": it.total_price,
            "show_in_kds": it.show_in_kds,
            "modifiers": parsed_mods  # 🎯 Add them to the response
        })

    # ---------------------------
    # Payment
    # ---------------------------
    payment = {}
    payment_doc = frappe.db.get_value(
        "Order Payment",
        {"order": order.name},
        ["payment_method", "platform", "amount", "transaction_id", "status"],
        as_dict=True
    )
    if payment_doc:
        payment = payment_doc

    # ---------------------------
    # Outlet & Restaurant
    # ---------------------------
    outlet = frappe.get_doc("Outlet", order.outlet, ignore_permissions=True)

    # ---------------------------
    # Response (NORMALIZED)
    # ---------------------------
    return {
        "order_id": order.name,
        "status": order.order_status,
        "payment_status": order.payment_status,

        "restaurant": order.restaurant,
        "outlet": order.outlet,
        "outlet_code": outlet.outlet_code,
        "storeName": outlet.outlet_code,

        "order_type": order.order_type,
        "platform": order.platform,

        "total_amount": order.total_amount,
        "tax_amount": order.tax_amount,
        "discount_amount": order.discount_amount,

        "items": items,
        "customer": customer,
        "payment": payment,

        "createdAt": order.creation,
        "updatedAt": order.modified
    }
    """
    Public API to fetch order status by order_id
    """

    if not order_id:
        frappe.throw("order_id is required")

    # Fetch order ignoring permissions (public tracking)
    order = frappe.get_value(
        "Order",
        order_id,
        [
            "name",
            "order_status",
            "payment_status",
            "total_amount",
            "platform",
            "order_type",
            "creation",
            "modified"
        ],
        as_dict=True
    )

    if not order:
        frappe.throw("Order not found")

    return {
        "order_id": order.name,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "order_type": order.order_type,
        "platform": order.platform,
        "total_amount": order.total_amount,
        "created_at": order.creation,
        "last_updated": order.modified
    }


@frappe.whitelist(allow_guest=True)
def mark_paid(order_id, transaction_id=None):
    """
    Marks an existing order as paid and releases it to the FOH/Kitchen!
    """
    if not order_id:
        frappe.throw("order_id is required")

    try:
        # 1. Fetch the order we just created
        order = frappe.get_doc("Order", order_id, ignore_permissions=True)
        
        # 2. Mark the money as received
        order.db_set("payment_status", "Paid")
        
        # 3. 🎯 THE FIX: Release the order to the restaurant staff!
        outlet = frappe.get_doc("Outlet", order.outlet, ignore_permissions=True)
        if outlet.auto_accept_orders:
            order.db_set("order_status", "Accepted") # Goes straight to Kitchen KDS
        else:
            order.db_set("order_status", "New") # Starts ringing on FOH Dashboard
            
        # Commit the changes
        frappe.db.commit()
        
        return {"success": True, "message": "Order successfully marked as paid!"}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Payment Error for {order_id}")
        frappe.throw(f"Failed to process payment: {str(e)}")