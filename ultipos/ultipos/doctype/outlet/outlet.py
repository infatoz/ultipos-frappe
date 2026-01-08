# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Outlet(Document):

    def before_insert(self):
        # Auto-set restaurant from logged-in user
        if not self.restaurant:
            user_restaurant = frappe.db.get_value(
                "User",
                frappe.session.user,
                "restaurant"
            )

            if not user_restaurant:
                frappe.throw("Restaurant is not assigned to your user")

            self.restaurant = user_restaurant

    def validate(self):
        if self.status == "Inactive":
            self.is_accepting_orders = 0
