console.log("✅ QZ INIT STARTED");

// 1️⃣ Load QZ JS (you already do this correctly)
(function () {
    if (window.qz) return;
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/qz-tray@2.2.5/qz-tray.js";
    script.onload = () => console.log("✅ QZ Tray JS loaded");
    document.head.appendChild(script);
})();

// 2️⃣ Certificate (must return TEXT)
qz.security.setCertificatePromise(function () {
    return fetch("/assets/ultipos/qz-cert.pem")
        .then(res => res.text());
});

// 3️⃣ ✅ CORRECT SIGNATURE PROMISE (IMPORTANT)
qz.security.setSignaturePromise(function (toSign) {
    return new Promise(function (resolve, reject) {
        fetch("/api/method/ultipos.qz.sign", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ data: toSign })
        })
        .then(res => {
            if (!res.ok) throw new Error("Sign failed");
            return res.text();
        })
        .then(signature => {
            resolve(signature);   // ✅ MUST resolve STRING
        })
        .catch(err => {
            console.error("❌ QZ SIGN ERROR", err);
            reject(err);
        });
    });
});
