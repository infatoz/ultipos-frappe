console.log("🚀 Order List JS loaded");

frappe.listview_settings["Order"] = {
    onload() {
        console.log("👂 Listening for KOT events...");

        frappe.realtime.on("kot_print", payload => {
            console.log("🚨 KOT EVENT RECEIVED", payload);

            frappe.show_alert(
                { message: `🧾 New Order ${payload.order_number}`, indicator: "green" },
                5
            );

            window.print_kot_qz(payload);
        });
    }
};
