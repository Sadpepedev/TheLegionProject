import requests

def fetch_token_price():
    url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
    params = {
        "contract_addresses": "0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c",
        "vs_currencies": "usd",
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-ZidvJFzBx9dCpeaGcZLohYHh"  # Use a valid key here
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        data = response.json()
        price = data.get("0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c", {}).get("usd")
        if price:
            print(f"Token Price in USD: ${price}")
            return price
        else:
            print("Token price not found in the response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the token price: {e}")
        return None

# Fetch the token price
fetch_token_price()
