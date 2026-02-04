console.log("🔥 QZ LOADER LOADED");

window.ensureQZ = async function () {
    // 1️⃣ Load QZ JS if not present
    if (!window.qz) {
        await new Promise((resolve, reject) => {
            const s = document.createElement("script");
            s.src = "https://cdn.jsdelivr.net/npm/qz-tray@2.2.5/qz-tray.js";
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
        console.log("✅ QZ JS loaded");
    }

    // 2️⃣ Connect once
    if (!qz.websocket.isActive()) {
        console.log("🔌 Connecting QZ...");
        await qz.websocket.connect();
        console.log("✅ QZ CONNECTED");
    }
};
