import frappe


def before_insert_order(doc, method=None):
    """
    Copy Menu Item printer config → Order Item
    """
    for row in doc.order_item:

        if row.printer:
            continue

        if not row.menu_item:
            continue

        menu_item = frappe.get_doc("Menu Item", row.menu_item)

        # 1️⃣ Item-level printer config
        if menu_item.item_printers:
            for cfg in menu_item.item_printers:
                if cfg.printer:
                    row.printer = cfg.printer
                    break
