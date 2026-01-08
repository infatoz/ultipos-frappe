frappe.realtime.on("ultipos_new_order", async (data) => {
    const currentOutlet = frappe.boot.user.outlet;

    // Only print for this outlet
    if (data.outlet !== currentOutlet) return;

    await silentPrintOrder(data.order_id);
});
