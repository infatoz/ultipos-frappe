# Copyright (c) 2026, Infatoz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Order(Document):

	def after_insert(self):
		frappe.publish_realtime(
            event="ultipos_new_order",
            message={
                "order_id": self.name,
                "outlet": self.outlet
            },
            after_commit=True
        )
