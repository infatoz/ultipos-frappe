# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Restaurant(Document):
	
    def after_insert(self):
		# Bind restaurant to owner user
        frappe.db.set_value(
            "User",
            self.owner_user,
            "restaurant",
            self.name
        )
    
    def validate(self):
        if frappe.db.exists(
			"Restaurant",
			{"owner_user": self.owner_user}
		): frappe.throw("This user already owns a restaurant")

