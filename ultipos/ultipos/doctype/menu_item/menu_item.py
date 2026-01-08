# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MenuItem(Document):

    def before_insert(self):
        self.restaurant = frappe.db.get_value(
            "User", frappe.session.user, "restaurant"
        )

    def validate(self):
        # Apply category defaults if enabled
        if self.inherit_category_config:
            self.apply_category_defaults()

        # Validation rules
        if self.inherit_category_config:
            if self.item_printers:
                frappe.throw(
                    "Item printers should be empty when inheriting category configuration."
                )
            if self.item_modifier_groups:
                frappe.throw(
                    "Item modifier groups should be empty when inheriting category configuration."
                )
        else:
            if not self.item_printers:
                frappe.throw(
                    "At least one printer is required when not inheriting category configuration."
                )

    def apply_category_defaults(self):
        category = frappe.get_doc("Menu Category", self.category)

        # 1️⃣ KDS inheritance
        if self.show_in_kds is None:
            self.show_in_kds = category.show_in_kds

        # 2️⃣ Printers
        self.item_printers = []
        for p in category.category_printers:
            self.append("item_printers", {
                "printer": p.printer,
                "copies": p.copies
            })

        # 3️⃣ Modifier Groups
        self.item_modifier_groups = []
        for m in category.category_modifier_groups:
            self.append("item_modifier_groups", {
                "modifier_group": m.modifier_group,
                "min_qty": m.min_qty,
                "max_qty": m.max_qty,
                "required": m.required
            })


# class MenuItem(Document):

#     def before_insert(self):
#         self.restaurant = frappe.db.get_value("User", frappe.session.user, "restaurant")

#     def validate(self):
#         # If inheriting category config, item-level configs must be empty
#         if self.inherit_category_config:
#             if self.item_printers:
#                 frappe.throw(
#                     "Item printers should be empty when inheriting category configuration."
#                 )
#             if self.item_modifier_groups:
#                 frappe.throw(
#                     "Item modifier groups should be empty when inheriting category configuration."
#                 )

#         # If NOT inheriting category config, item must define its own printers
#         else:
#             if not self.item_printers:
#                 frappe.throw(
#                     "At least one printer is required when not inheriting category configuration."
#                 )


#     def apply_category_defaults(self):
#         category = frappe.get_doc("Menu Category", self.category)

#         # 1️⃣ KDS
#         if self.show_in_kds is None:
#             self.show_in_kds = category.show_in_kds

#         # 2️⃣ Printers
#         self.item_printers = []
#         for p in category.category_printers:
#             self.append("item_printers", {
#                 "printer": p.printer,
#                 "copies": p.copies
#             })

#         # 3️⃣ Modifier Groups
#         self.item_modifier_groups = []
#         for m in category.category_modifier_groups:
#             self.append("item_modifier_groups", {
#                 "modifier_group": m.modifier_group,
#                 "min_qty": m.min_qty,
#                 "max_qty": m.max_qty,
#                 "required": m.required
#             })
