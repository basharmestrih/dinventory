import requests
import json

url = "https://app.fawaterk.com/api/v2/invoiceInitPay"

payload = json.dumps({
  "payment_method_id": 4,
  "cartTotal": "100",
  "currency": "EGP",
  "customer": {
    "first_name": "test",
    "last_name": "test",
    "email": "test@test.com",
    "phone": "01035144208",
    "address": "test address"
  },
  "redirectionUrls": {
    "successUrl": "https://dev.fawaterk.com/success",
    "failUrl": "https://dev.fawaterk.com/fail",
    "pendingUrl": "https://dev.fawaterk.com/pending"
  },
  "cartItems": [
    {
      "name": "test",
      "price": "100",
      "quantity": "1"
    }
  ]
})
headers = {
  'Authorization': 'Bearer 7fc8623139a5578670f37893d540a05da1954ae61267d0f17e',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)