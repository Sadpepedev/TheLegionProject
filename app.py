from flask import Flask, send_from_directory, request, jsonify
import requests
import os
import logging
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Limiter for rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# CoinGecko API endpoint and token details
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
TOKEN_CONTRACT_ADDRESS = "0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c"
SEED_ROUND_PRICE = 0.02  # Fixed seed round price in USD ($0.02 per token)

# Environment variables for API Key (if required)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")  # Ensure this is set in your environment

# Cache variables
cache = {
    "price": None,
    "timestamp": 0
}
CACHE_DURATION = 60  # seconds

def get_token_price():
    """
    Fetch the current token price from CoinGecko API.
    Implements caching to reduce API calls.
    Returns:
        float: The current token price in USD.
    """
    current_time = time.time()
    if cache["price"] and (current_time - cache["timestamp"] < CACHE_DURATION):
        logging.info("Using cached token price.")
        return cache["price"]
    
    params = {
        "contract_addresses": TOKEN_CONTRACT_ADDRESS,
        "vs_currencies": "usd",
    }
    headers = {"accept": "application/json"}

    # Include API key in headers if available
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        logging.info("Fetching token price from CoinGecko API...")
        response = requests.get(COINGECKO_API_URL, params=params, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        price = data.get(TOKEN_CONTRACT_ADDRESS, {}).get("usd")
        if price is not None:
            logging.info(f"Fetched token price: ${price}")
            cache["price"] = price
            cache["timestamp"] = current_time
            return price
        else:
            logging.error("Token price not found in the API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching token price: {e}")
        return None

@app.route("/")
def home():
    """
    Serve the index.html file from the static directory.
    Returns:
        HTML: The index.html file content.
    """
    try:
        return send_from_directory("static", "index.html")
    except Exception as e:
        logging.error(f"Error serving index.html: {e}")
        return "An error occurred while loading the page.", 500

@app.route("/calculate", methods=["POST"])
@limiter.limit("10 per minute")  # Example rate limit
def calculate():
    """
    Handle the ROI calculation based on user input.
    Returns:
        JSON: ROI calculation results.
    """
    try:
        # Parse user input
        data = request.get_json()
        investment_input = data.get("investment")
        
        if investment_input is None:
            logging.error("Investment input is missing.")
            return jsonify({"error": "Investment input is missing."}), 400
        
        try:
            initial_investment = float(investment_input)
            if initial_investment <= 0:
                raise ValueError("Investment must be greater than zero.")
        except (TypeError, ValueError) as e:
            logging.error(f"Invalid investment input: {e}")
            return jsonify({"error": str(e)}), 400

        # Fetch the current token price
        current_price = get_token_price()

        if current_price is None:
            return jsonify({"error": "Failed to fetch current token price."}), 500

        # Calculate ROI
        tokens_purchased = initial_investment / SEED_ROUND_PRICE
        roi_value = tokens_purchased * current_price

        # Log calculation details
        logging.info(f"ROI Calculation - Investment: ${initial_investment}, "
                     f"Tokens Purchased: {tokens_purchased}, Current Price: ${current_price}, ROI: ${roi_value}")

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })
    except Exception as e:
        logging.error(f"Error in calculate route: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == "__main__":
    # Run the Flask application
    app.run(debug=False)
