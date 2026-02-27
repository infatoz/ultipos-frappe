import frappe
from frappe.utils import now


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
    printers = get_kot_printers()
    if not printers:
        return None

    items = [
        {
            "qty": row.qty,
            "name": row.item_name,
            "note": row.notes or ""
        }
        for row in order.order_item
    ]

    return {
        "order_number": order.name,
        "kot_time": now(),
        "printers": [
            {
                "printer_ip": p.printer_identifier,
                "items": items
            }
            for p in printers
        ]
    }


def publish_kot(order):
    payload = build_payload(order)
    if payload:
        frappe.publish_realtime("kot_print", payload)


# =========================================
# EVENTS
# =========================================

def on_order_created(doc, method=None):
    """
    ONLY change status here
    NEVER print here
    """
    auto_accept = True

    if auto_accept:
        doc.db_set("order_status", "Accepted")   # triggers on_update


def on_status_change(doc, method=None):
    """
    PRINT ONLY ONCE WHEN ACCEPTED
    """

    # 🔥 critical: only print when status JUST changed
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
