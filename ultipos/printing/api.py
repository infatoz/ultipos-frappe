import frappe
from ultipos.printing.templates import generate_test_kot

@frappe.whitelist()
def test_printer(printer):
    p = frappe.get_doc("Printer", printer)

    payload = generate_test_kot(
        p.printer_name,
        p.paper_width
    )

    return {
        "printer": p.printer_identifier,
        "port": p.port,
        "payload": payload
    }


@frappe.whitelist()
def test_kot_before_submit(printer_name, paper_width):
    """
    Test KOT printing BEFORE Printer doc is saved
    """
    payload = generate_test_kot(
        printer_name=printer_name,
        width=paper_width
    )

    return {
        "payload": payload
    }

@frappe.whitelist()
def get_order_kot_jobs(order_id):
    return get_kot_print_jobs(order_id)
