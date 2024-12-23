python -m pip install requests
import requests

url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c&vs_currencies=usd"

headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": "CG-ZidvJFzBx9dCpeaGcZLohYHh\t"
}

response = requests.get(url, headers=headers)

print(response.text)
