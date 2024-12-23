from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")  

def get_token_price():
    url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
    params = {
        "contract_addresses": "0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c",
        "vs_currencies": "usd",
    }
    headers = {"accept": "application/json"}
    
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        price = data.get("0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c", {}).get("usd")
        if price:
            logging.info(f"Fetched token price: ${price}")
            return price
        else:
            logging.error("Token price not found in the API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching token price: {e}")
        return None

@app.route("/")
def home():
    try:
        token_price = get_token_price()
        return render_template("index.html", token_price=token_price)
    except Exception as e:
        logging.error(f"Error rendering home page: {e}")
        return "An error occurred while loading the page.", 500

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
      
        data = request.json
        initial_investment = float(data.get("investment", 0))
        round_price = float(data.get("round_price", 0.02))  # Fixed seed price: 0.02

        if initial_investment <= 0 or round_price <= 0:
            return jsonify({"error": "Investment and round price must be greater than zero."}), 400

        # Fetch the current token price
        current_price = get_token_price()

        if current_price is None:
            return jsonify({"error": "Failed to fetch current token price."}), 500

        # Calculate ROI
        tokens_purchased = initial_investment / round_price
        roi_value = tokens_purchased * current_price

        logging.info(f"ROI Calculation - Investment: ${initial_investment}, Round Price: ${round_price}, Current Price: ${current_price}, ROI: ${roi_value}")

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })
    except Exception as e:
        logging.error(f"Error in calculate route: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

# Main function
if __name__ == "__main__":
    app.run(debug=True)
