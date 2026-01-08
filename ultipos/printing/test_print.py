def generate_test_kot(printer):
    return f"""
    *** TEST KOT ***
    UltiPOS Printer Test

    Item: Test Burger x1
    Item: Test Coke x1

    Kitchen Printer OK
    -------------------
    """

def generate_test_receipt(printer):
    return f"""
    *** TEST RECEIPT ***
    UltiPOS

    Test Item        100
    -------------------
    TOTAL           100

    Thank you!
    """

def enqueue_test_print(printer, job_type):
    payload = (
        generate_test_kot(printer)
        if job_type == "KOT"
        else generate_test_receipt(printer)
    )

    job = frappe.new_doc("Print Job")
    job.printer = printer.name
    job.job_type = "Test"
    job.payload = payload
    job.status = "Pending"
    job.insert(ignore_permissions=True)

# def create_kot_print_jobs(order):
#     for item in order.items:
#         printer = item.printer  # snapshot
#         payload = build_kot_payload(order, item)

#         job = frappe.new_doc("Print Job")
#         job.printer = printer
#         job.outlet = order.outlet
#         job.job_type = "KOT"
#         job.payload = payload
#         job.status = "Pending"
#         job.insert(ignore_permissions=True)
