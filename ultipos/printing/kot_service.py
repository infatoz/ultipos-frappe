import frappe

def get_kot_print_jobs(order_id):
    """
    Returns list of printers & payloads for the order
    """
    order = frappe.get_doc("Order", order_id)

    jobs = []

    for item in order.items:
        if not item.show_in_kds:
            continue

        payload = build_kot_payload(order, item)

        jobs.append({
            "printer": item.printer_identifier,  # snapshot
            "port": item.printer_port or 9100,
            "payload": payload
        })

    return jobs
