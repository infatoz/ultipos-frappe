import requests
import frappe


def worldline_create_payment(settings, amount, customer):
    """
    Create Worldline payment request
    """
    url = "https://payment.worldline.com/api/payments"

    payload = {
        "amount": amount,
        "currency": "INR",
        "customer": {
            "email": customer.get("email"),
            "phone": customer.get("phone")
        },
        "merchantId": settings.merchant_id
    }

    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json()["redirectUrl"]
