// QZ Tray Security Configuration
qz.security.setCertificatePromise(() => {
    return fetch("/assets/ultipos/qz-cert.pem").then(res => res.text());
});

qz.security.setSignaturePromise((toSign) => {
    return fetch("/api/method/ultipos.qz.sign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: toSign })
    }).then(res => res.text());
});
