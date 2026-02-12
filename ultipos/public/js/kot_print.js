// console.log("🔥 KOT Bridge Listener Started");

// const BRIDGE_URL = "http://127.0.0.1:8181/print";

// async function sendToBridge(payload) {
//     try {
//         console.log("🧾 Sending to bridge →", payload);

//         await fetch(BRIDGE_URL, {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify(payload)
//         });

//         console.log("✅ Sent to local bridge");

//     } catch (e) {
//         console.error("❌ Bridge not reachable", e);

//         frappe.show_alert({
//             message: "Print Bridge not running",
//             indicator: "red"
//         });
//     }
// }

// /* GLOBAL realtime listener */
// frappe.realtime.on("kot_print", payload => {
//     console.log("🧾 KOT event received → sending", payload);
//     sendToBridge(payload);
// });


console.log("🔥 KOT Bridge Listener Booting...");

const BRIDGE_URL = "http://127.0.0.1:8181/print";

/* =========================================
   SEND TO FLUTTER BRIDGE
========================================= */
async function sendToBridge(payload) {

    console.log("🧾 Sending to bridge →", payload);

    try {
        await fetch(BRIDGE_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        console.log("✅ Sent to local bridge");

    } catch (e) {
        console.error("❌ Bridge not reachable", e);
    }
}

/* =========================================
   WAIT FOR SOCKET CONNECTION
========================================= */

function attachRealtimeListener() {

    if (!frappe.realtime || !frappe.realtime.socket) {
        console.log("⏳ Waiting for realtime socket...");
        setTimeout(attachRealtimeListener, 500);
        return;
    }

    console.log("✅ Realtime socket connected. Attaching KOT listener...");

    frappe.realtime.on("kot_print", payload => {
        console.log("🧾 KOT event received → sending", payload);
        sendToBridge(payload);
    });
}

attachRealtimeListener();
