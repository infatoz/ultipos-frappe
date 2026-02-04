import frappe
from frappe.utils import now
import json

@frappe.whitelist()
def publish_kot(order_name, method=None):
    order = frappe.get_doc("Order", order_name)
    print("Publishing KOT for order:", order.as_json())

    printer = frappe.get_all(
        "Printer",
        filters={
            "is_active": 1,
            "printer_role": ["in", ["KOT", "Both"]],
            "status": ["!=", "Disabled"]
        },
        fields=["printer_identifier"],
        limit=1
    )

    if not printer:
        frappe.throw("No active KOT printer found")

    items = []
    for i in order.order_item:
        items.append({
            "item_name": i.item_name,
            "qty": i.qty,
            "note": i.notes or ""
        })

    payload = {
        "order_number": order.name,
        "kot_time": now(),
        "printers": [{
            "printer_name": printer[0].printer_identifier,  # IP
            "items": items
        }]
    }

    frappe.publish_realtime("kot_print", payload)
    return payload
