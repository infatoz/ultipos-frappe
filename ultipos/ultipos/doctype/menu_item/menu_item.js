// Copyright (c) 2026, Infatoz Technologies LLP and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Menu Item", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Menu Item", {
  category(frm) {
    if (!frm.doc.category) return;

    frappe.call({
      method: "ultipos.menu.get_category_defaults",
      args: {
        category: frm.doc.category
      },
      callback(r) {
        if (!r.message) return;

        const data = r.message;

        // 1️⃣ KDS visibility
        if (frm.doc.show_in_kds === undefined || frm.is_new()) {
          frm.set_value("show_in_kds", data.show_in_kds);
        }

        // 2️⃣ Printers
        frm.clear_table("item_printers");
        (data.printers || []).forEach(p => {
          let row = frm.add_child("item_printers");
          row.printer = p.printer;
          row.copies = p.copies;
        });

        // 3️⃣ Modifier Groups
        frm.clear_table("item_modifier_groups");
        (data.modifier_groups || []).forEach(m => {
          let row = frm.add_child("item_modifier_groups");
          row.modifier_group = m.modifier_group;
          row.min_qty = m.min_qty;
          row.max_qty = m.max_qty;
          row.required = m.required;
        });

        frm.refresh_fields();
      }
    });
  }
});

