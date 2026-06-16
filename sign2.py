import requests
import json

url = "https://dev.fawaterk.com/api/v2/getPaymentmethods"

payload={}
headers = {
  'content-type': 'application/json',
  'Authorization': 'Bearer a65c827f20907f2cce89c89e1069fb5df983a33330b78cc570'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)