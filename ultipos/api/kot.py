import frappe
from frappe.utils import now
import json

def build_payload(order):
    printer_routing = {}

    for row in order.order_item:
        try:
            menu_item_doc = frappe.get_doc("Menu Item", row.menu_item)
        except Exception:
            continue

        printer_configs = menu_item_doc.get("item_printers") or []

        # Parse modifiers safely for both routes
        parsed_mods = []
        if row.modifiers:
            try:
                parsed_mods = json.loads(row.modifiers)
            except:
                pass

        # 🎯 SMALL STORE FALLBACK: If they didn't assign a printer, send it to 'Main Station'
        if len(printer_configs) == 0:
            if "Main Station" not in printer_routing:
                printer_routing["Main Station"] = []
            
            printer_routing["Main Station"].append({
                "qty": row.qty,
                "name": row.item_name,
                "note": row.notes or "",
                "modifiers": parsed_mods
            })
            continue # Move to the next item

        # 🎯 BIG STORE ROUTING: Process assigned printers
        for config in printer_configs:
            assigned_printer = config.printer

            if assigned_printer:
                if assigned_printer not in printer_routing:
                    printer_routing[assigned_printer] = []

                printer_routing[assigned_printer].append({
                    "qty": row.qty,
                    "name": row.item_name,
                    "note": row.notes or "",
                    "modifiers": parsed_mods
                })
    printers_payload = []
    for p_key, items in printer_routing.items():
        printers_payload.append({
            "printer_name": p_key, 
            "items": items
        })

    if not printers_payload:
        return None

    return {
        "order_number": order.name,
        "order_type": order.order_type,
        "kot_time": now(),
        "printers": printers_payload
    }


def publish_kot(order):
    payload = build_payload(order)
    
    if payload:
        # 🖨️ --- CONSOLE TESTING BLOCK --- 🖨️
        print("\n" + "="*60)
        print(f"🔥 KOT ROUTING TRIGGERED FOR: {order.name} 🔥")
        print(json.dumps(payload, indent=4))
        print("="*60 + "\n")
        
        # Broadcast via WebSockets (Socket.io) to the React KDS!
        frappe.publish_realtime("kot_print", payload)

# =========================================
# DATABASE EVENTS (Triggered via hooks.py)
# =========================================

def on_order_created(doc, method=None):
    """Triggered when order.py creates an order with Auto-Accept ON"""
    if doc.order_status == "Accepted":
        publish_kot(doc)

def on_status_change(doc, method=None):
    """Triggered by order_manager.py when a human clicks 'Accept'"""
    old_doc = doc.get_doc_before_save()
    if not old_doc: return
    
    # 🎯 Only trigger if it literally JUST changed to "Accepted"
    if doc.order_status == "Accepted" and old_doc.order_status != "Accepted":
        publish_kot(doc)