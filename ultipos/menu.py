import frappe

@frappe.whitelist()
def get_category_defaults(category):
    """
    Returns printer, KDS, and modifier defaults for a category
    """

    cat = frappe.get_doc("Menu Category", category)

    printers = []
    for p in cat.category_printers:
        printers.append({
            "printer": p.printer,
            "copies": p.copies
        })

    modifier_groups = []
    for m in cat.category_modifier_groups:
        modifier_groups.append({
            "modifier_group": m.modifier_group,
            "min_qty": m.min_qty,
            "max_qty": m.max_qty,
            "required": m.required
        })

    return {
        "show_in_kds": cat.show_in_kds,
        "printers": printers,
        "modifier_groups": modifier_groups
    }
