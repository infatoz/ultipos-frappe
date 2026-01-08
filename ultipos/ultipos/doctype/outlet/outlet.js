// Copyright (c) 2026, Infatoz Technologies LLP and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Outlet", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Outlet", {
  onload(frm) {
    if (!frm.doc.restaurant) {
      frm.set_value("restaurant", frappe.session.user.restaurant);
      frm.toggle_enable("restaurant", false);
    }
  }
});

