frappe.ui.form.on("Printer", {
    refresh(frm) {
        // Show Detect button for both Network and USB if in Draft
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button("Detect Printers", async () => {
                await detectPrinters(frm);
            });

            frm.add_custom_button("Test KOT Print", async () => {
                await testKOTBeforeSubmit(frm);
            });
        }
    },
    
    // Auto-connect to QZ when the form opens to save time
    onload(frm) {
        if (typeof qz !== "undefined" && !qz.websocket.isActive()) {
            qz.websocket.connect().catch(err => console.error("QZ Connection Error:", err));
        }
    }
});

async function detectPrinters(frm) {
    if (typeof qz === "undefined") {
        frappe.msgprint(__("❌ QZ Tray is not running."));
        return;
    }

    try {
        if (!qz.websocket.isActive()) await qz.websocket.connect();

        const printers = await qz.printers.find();

        if (printers && printers.length > 0) {
            // 1. Update the dropdown list options
            frm.set_df_property("printer_identifier", "options", printers);

            // 2. AUTO-SELECT: Pick the first printer if the field is empty
            if (!frm.doc.printer_identifier) {
                frm.set_value("printer_identifier", printers[0]);
            }

            frappe.show_alert({message: __("✅ {0} printers detected", [printers.length]), indicator: 'green'});
        } else {
            frappe.msgprint(__("No printers found on this system."));
        }
    } catch (e) {
        console.error(e);
        frappe.msgprint(__("❌ Failed to detect printers"));
    }
}

// async function detectPrinters(frm) {
//     if (typeof qz === "undefined") {
//         frappe.msgprint(__("❌ QZ Tray is not running or installed."));
//         return;
//     }

//     try {
//         if (!qz.websocket.isActive()) await qz.websocket.connect();

//         const printers = await qz.printers.find();

//         if (printers && printers.length > 0) {
//             // Update the dropdown options
//             frm.set_df_property("printer_identifier", "options", [""].concat(printers));
//             frm.refresh_field("printer_identifier");
//             frappe.show_alert({message: __("Printers detected"), indicator: 'green'});
//         } else {
//             frappe.msgprint(__("No printers found on this system."));
//         }
//     } catch (e) {
//         frappe.msgprint(__("Error connecting to QZ Tray: ") + e.message);
//     }
// }

async function testKOTBeforeSubmit(frm) {
    // 1. Validation Check
    // if (!frm.doc.printer_identifier) {
    //     frappe.msgprint({
    //         title: __('Selection Required'),
    //         indicator: 'orange',
    //         message: __('Please click "Detect Printers" and select a printer from the list first.')
    //     });
    //     return;
    // }

    try {
        if (!qz.websocket.isActive()) await qz.websocket.connect();

        frappe.dom.freeze(__('Printing Test KOT...'));

        const res = await frappe.call({
            method: "ultipos.printing.api.test_kot_before_submit",
            args: {
                printer_name: frm.doc.printer_name || "Test Printer",
                paper_width: frm.doc.paper_width || "80"
            }
        });

        print("Test KOT", res);

        if (res.message && res.message.payload) {
            const config = qz.configs.create(frm.doc.printer_identifier, {
                encoding: "raw",
                port: frm.doc.port || 9100,
                forceWait: false, // Helps with speed
    silent: true      // <--- THIS ENABLES SILENT PRINTING
            });

            await qz.print(config, [res.message.payload]);
            
            // Mark as tested and enable submission
            frm.doc.__kot_tested = true;
            frappe.msgprint(__("✅ Test KOT sent to {0}", [frm.doc.printer_identifier]));
        }
    } catch (err) {
        console.error(err);
        frappe.msgprint(__("❌ Printing failed: ") + (err.message || err));
    } finally {
        frappe.dom.unfreeze();
    }
}