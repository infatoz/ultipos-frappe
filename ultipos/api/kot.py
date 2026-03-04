import frappe
from frappe.utils import now
import json

# =========================================
# HELPERS
# =========================================

def get_kot_printers():
    return frappe.get_all(
        "Printer",
        filters={
            "is_active": 1,
            "printer_role": ["in", ["KOT", "Both"]],
            "status": ["!=", "Disabled"]
        },
        fields=["printer_identifier"]
    )


def build_payload(order):
    # This dictionary acts as our "sorting buckets" for different printers
    printer_routing = {}

    for row in order.order_item:
        # 1. Fetch the full Menu Item document so we can look inside its tables
        try:
            menu_item_doc = frappe.get_doc("Menu Item", row.menu_item)
        except Exception:
            continue

        # 2. Pull from 'item_printers' based on your screenshot!
        printer_configs = menu_item_doc.get("item_printers") or []

        for config in printer_configs:
            # This is exactly "MTRPrinter" or "printer2"
            assigned_printer = config.printer

            if assigned_printer:
                # 🎯 FIXED: We skip checking for an IP address and just use the name!
                printer_key = assigned_printer

                # 4. Create a bucket for this Printer if it doesn't exist yet
                if printer_key not in printer_routing:
                    printer_routing[printer_key] = []

                # 5. Drop the item into the correct printer's bucket
                printer_routing[printer_key].append({
                    "qty": row.qty,
                    "name": row.item_name,
                    "note": row.notes or ""
                })

    # 6. Convert our buckets back into the list format
    printers_payload = []
    for p_key, items in printer_routing.items():
        printers_payload.append({
            "printer_ip": p_key, # We are sending the printer name here for testing
            "items": items
        })

    # If no items had valid printers, abort the print job
    if not printers_payload:
        return None

    return {
        "order_number": order.name,
        "kot_time": now(),
        "printers": printers_payload
    }


def publish_kot(order):
    payload = build_payload(order)
    
    if payload:
        # 🖨️ --- CONSOLE TESTING BLOCK --- 🖨️
        print("\n" + "="*60)
        print(f"🔥 KOT ROUTING TRIGGERED FOR: {order.name} 🔥")
        print("Here are the split tickets going to the printers:")
        print(json.dumps(payload, indent=4))
        print("="*60 + "\n")
        # -----------------------------------
        
        # This sends it to the frontend/hardware (Leave this here!)
        frappe.publish_realtime("kot_print", payload)

# =========================================
# EVENTS
# =========================================

def on_order_created(doc, method=None):
    """
    Auto accept flow (Uber style)
    """
    auto_accept = True

    if auto_accept:
        # We JUST change the status here. 
        # Frappe will automatically trigger on_status_change for us right after this!
        doc.order_status = "Accepted"
        
        # ❌ REMOVED: publish_kot(doc) 

def on_status_change(doc, method=None):
    """
    Manual accept/deny (If auto-accept is turned off later)
    OR triggered automatically by on_order_created!
    """
    # Only print if the status literally just changed to Accepted
    if doc.has_value_changed("order_status") and doc.order_status == "Accepted":
        publish_kot(doc)

# =========================================
# ACTION BUTTONS
# =========================================

@frappe.whitelist()
def accept_order(order_name):
    doc = frappe.get_doc("Order", order_name)
    doc.order_status = "Accepted"
    doc.save(ignore_permissions=True)   # only ONE save
    frappe.db.commit()


@frappe.whitelist()
def deny_order(order_name):
    doc = frappe.get_doc("Order", order_name)
    doc.order_status = "Cancelled"
    doc.save(ignore_permissions=True)
    frappe.db.commit()


# import frappe
# from frappe.utils import now

# # =====================================================
# # HELPERS
# # =====================================================

# def get_kot_printers():
#     """
#     Fetch active KOT printers (IP stored in printer_identifier)
#     """
#     return frappe.get_all(
#         "Printer",
#         filters={
#             "is_active": 1,
#             "printer_role": ["in", ["KOT", "Both"]],
#             "status": ["!=", "Disabled"]
#         },
#         fields=["printer_identifier"]
#     )


# def build_payload(order):
#     printers = get_kot_printers()
#     if not printers:
#         return None

#     items = [
#         {
#             "qty": row.qty,
#             "name": row.item_name,
#             "note": row.notes or ""
#         }
#         for row in order.order_item
#     ]

#     return {
#         "order_number": order.name,
#         "kot_time": now(),
#         "printers": [
#             {
#                 "printer_ip": p.printer_identifier,
#                 "items": items
#             }
#             for p in printers
#         ]
#     }


# def publish_kot(order):
#     payload = build_payload(order)
#     if payload:
#         frappe.publish_realtime("kot_print", payload)


# # =====================================================
# # EVENTS
# # =====================================================

# def on_order_created(doc, method=None):
#     """
#     Auto accept flow (Uber style)
#     """

#     auto_accept = True  # or from settings

#     if auto_accept:
#         doc.db_set("order_status", "Accepted")
#         publish_kot(doc)


# def on_status_change(doc, method=None):
#     """
#     Manual accept/deny
#     """

#     if doc.order_status == "Accepted":
#         publish_kot(doc)

#     if doc.order_status == "Cancelled":
#         frappe.logger().info(f"Order {doc.name} cancelled")


# @frappe.whitelist()
# def test_kot():
#     frappe.publish_realtime(
#         "kot_print",
#         {
#             "order_number": "TEST-001",
#             "printers": [
#                 {
#                     "printer_ip": "192.168.0.100",
#                     "items": [
#                         {"qty": 1, "name": "Coffee"},
#                         {"qty": 2, "name": "Burger"}
#                     ]
#                 }
#             ]
#         }
#     )


# @frappe.whitelist()
# def accept_order(order_name):
#     doc = frappe.get_doc("Order", order_name)
#     doc.order_status = "Accepted"
#     doc.save()          # ✅ triggers on_update
#     frappe.db.commit()


# @frappe.whitelist()
# def deny_order(order_name):
#     doc = frappe.get_doc("Order", order_name)
#     doc.order_status = "Cancelled"
#     doc.save()          # ✅ triggers on_update
#     frappe.db.commit()
