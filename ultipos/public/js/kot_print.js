console.log("🔥 KOT PRINT JS LOADED");

window.print_kot_qz = async function (payload) {
    console.log("🖨️ PRINTING KOT", payload);

    try {
        await ensureQZ(); // 🔑 IMPORTANT

        for (const p of payload.printers) {
            const config = qz.configs.create({
                host: p.printer_name,
                port: 9100,
                forceRaw: true
            });

            const data = [
                "\x1B\x40",
                "\x1B\x61\x01",
                "KOT\n",
                "----------------------\n",
                `Order: ${payload.order_number}\n`,
                "----------------------\n"
            ];

            p.items.forEach(i => {
                data.push(`${i.qty} x ${i.item_name}\n`);
            });

            data.push("\n\n\n\x1D\x56\x00");

            await qz.print(config, data);
        }

        console.log("✅ KOT PRINT SUCCESS");
    } catch (e) {
        console.error("❌ KOT PRINT FAILED", e);
        frappe.show_alert({
            message: "Printer / QZ error",
            indicator: "red"
        });
    }
};
