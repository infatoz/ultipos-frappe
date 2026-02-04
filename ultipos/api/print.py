import frappe

@frappe.whitelist()
def get_pending_kot():
    """Returns the oldest pending KOT and marks it as fetched"""
    # Find one pending print job
    job = frappe.db.get_value("Print Queue", {"status": "Pending"}, ["name", "print_data"], as_dict=1)
    
    if job:
        # Mark as sent so it doesn't print twice
        frappe.db.set_value("Print Queue", job.name, "status", "Printed")
        frappe.db.commit()
        return {"kot_text": job.print_data}
    
    return None