import frappe
from frappe.model.document import Document

class Menu(Document):

    def before_validate(self):
        # This runs BEFORE the mandatory field check
        self._set_restaurant()

    def validate(self):
        # This runs AFTER the fields are populated
        self._validate_restaurant()
        
        user = frappe.session.user
        user_outlet = frappe.db.get_value("User", user, "outlet")

        if user_outlet and self.outlet != user_outlet:
            frappe.throw("You can only manage menus for your outlet")
    

    def _set_restaurant(self):
        # If already set (e.g., by an Admin), don't overwrite
        if self.restaurant:
            return

        user = frappe.session.user
        user_type = frappe.db.get_value("User", user, "user_type")

        # System Users (Admins) might not have a restaurant link
        if user_type == "System User":
            return 

        user_restaurant = frappe.db.get_value("User", user, "restaurant")

        if not user_restaurant:
            frappe.throw("Restaurant is not assigned to your user profile")

        self.restaurant = user_restaurant
        print("Set restaurant to:", self.restaurant)

    def _validate_restaurant(self):
        user = frappe.session.user
        user_type = frappe.db.get_value("User", user, "user_type")

        if user_type == "System User":
            return

        user_restaurant = frappe.db.get_value("User", user, "restaurant")

        if self.restaurant != user_restaurant:
            frappe.throw("You cannot assign menu to another restaurant")