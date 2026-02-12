frappe.listview_settings["Order"] = {

    onload(listview) {

        console.log("🔥 Order list loaded");

        // ACCEPT
        listview.page.add_action_item("Accept Order", async () => {

            const doc = listview.get_checked_items()[0];
            if (!doc) return;

            await frappe.call({
                method: "ultipos.api.kot.accept_order",
                args: { order_name: doc.name }
            });

            frappe.show_alert("Order Accepted");
            listview.refresh();
        });


        // DENY
        listview.page.add_action_item("Deny Order", async () => {

            const doc = listview.get_checked_items()[0];
            if (!doc) return;

            await frappe.call({
                method: "ultipos.api.kot.deny_order",
                args: { order_name: doc.name }
            });

            frappe.show_alert("Order Cancelled");
            listview.refresh();
        });
    }
};
