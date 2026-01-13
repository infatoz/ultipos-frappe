# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def get_user_restaurant(user):
    return frappe.db.get_value(
        "Restaurant User",
        {"user": user, "role": "Owner"},
        "restaurant"
    )

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


# import frappe
# from frappe.model.document import Document

# def get_user_restaurant(user):
#     return frappe.db.get_value(
#         "Restaurant User",
#         {"user": user, "role": "Owner"},
#         "restaurant"
#     )

# class Outlet(Document):

#     def before_insert(self):
#         # If restaurant already selected in UI, don't override
#         if self.restaurant:
#             return

#         user_restaurant = get_user_restaurant(frappe.session.user)

#         if not user_restaurant:
#             frappe.throw(
#                 "Restaurant is not assigned to your user. "
#                 "Create a Restaurant User record for this user OR select restaurant manually."
#             )

#         self.restaurant = user_restaurant

#     def validate(self):
#         if self.status == "Inactive":
#             self.is_accepting_orders = 0
