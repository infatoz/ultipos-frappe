# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MenuAvailability(Document):
	def before_insert(self):
		self.restaurant = frappe.db.get_value(
			"User", frappe.session.user, "restaurant"
		)

