// Copyright (c) 2026, Infatoz Technologies LLP and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Order", {
// 	refresh(frm) {

// 	},
// });

async function silentPrintOrder(orderId) {
    if (typeof qz === "undefined") {
        console.error("QZ Tray not loaded");
        return;
    }

    try {
        if (!qz.websocket.isActive()) {
            await qz.websocket.connect();
        }

        const res = await frappe.call({
            method: "ultipos.printing.api.get_order_kot_jobs",
            args: { order_id: orderId }
        });

        const jobs = res.message || [];

        for (const job of jobs) {
            const config = qz.configs.create(
                job.printer,
                {
                    encoding: "raw",
                    port: job.port,
                    silent: true
                }
            );

            await qz.print(config, [job.payload]);
        }

        console.log("✅ KOT printed silently for order", orderId);

    } catch (err) {
        console.error("❌ Silent print failed", err);
    }
}
