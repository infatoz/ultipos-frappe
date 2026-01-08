# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Printer(Document):
	def before_insert(self):
		self.restaurant = frappe.db.get_value(
			"User", frappe.session.user, "restaurant"
		)
	
	def validate(self):
		if not self.kot_tested:
			frappe.throw("Printer must be tested before activation")

