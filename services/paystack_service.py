import requests
from flask import current_app

def initialize_transaction(email, amount, currency="NGN", reference=None, metadata=None):
    url = f"{current_app.config['PAYSTACK_BASE_URL']}/transaction/initialize"
    headers = {
        "Authorization": (f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}"),
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
        "amount": str(amount),
        "currency": currency,
        "reference": reference,
        "metadata": metadata or {},
    }