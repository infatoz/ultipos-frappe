(function () {
    if (window.qz) return;

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/qz-tray@2.2.5/qz-tray.js";
    script.type = "text/javascript";
    script.onload = () => console.log("✅ QZ Tray JS loaded");
    document.head.appendChild(script);
})();
