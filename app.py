from flask import Flask, send_from_directory, request, jsonify
import requests
import os
import logging
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file (if present)
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Logs to stdout
    ]
)

# Initialize Limiter for rate limiting without passing 'app'
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Associate Limiter with the Flask app
limiter.init_app(app)

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

# Setup a requests session with retry strategy
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)

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
        "contract_addresses": TOKEN_CONTRACT_ADDRESS.lower(),
        "vs_currencies": "usd",
    }
    headers = {"accept": "application/json"}

    # Include API key in headers if available
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        logging.info("Fetching token price from CoinGecko API...")
        response = session.get(COINGECKO_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        logging.debug(f"API Response: {data}")
        price = data.get(TOKEN_CONTRACT_ADDRESS.lower(), {}).get("usd")  # Ensure contract address is lowercase
        if price is not None:
            logging.info(f"Fetched token price: ${price}")
            cache["price"] = price
            cache["timestamp"] = current_time
            return price
        else:
            logging.error("Token price not found in the API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching token price: {e}", exc_info=True)
        return None

@app.route("/")
def home():
    """
    Serve the index.html file from the root directory.
    """
    try:
        logging.info("Serving index.html from the root directory.")
        return send_from_directory(".", "index.html")
    except FileNotFoundError:
        logging.error("index.html not found in the root directory.")
        return "index.html not found.", 404
    except Exception as e:
        logging.error(f"Error serving index.html: {e}", exc_info=True)
        return "An error occurred while loading the page.", 500


@app.route("/fuel.html")
def serve_fuel():
    """
    Serve the fuel.html file from the root directory.
    """
    try:
        logging.info("Serving fuel.html from the root directory.")
        return send_from_directory(".", "fuel.html")
    except FileNotFoundError:
        logging.error("fuel.html not found in the root directory.")
        return "fuel.html not found.", 404
    except Exception as e:
        logging.error(f"Error serving fuel.html: {e}", exc_info=True)
        return "An error occurred while loading the page.", 500


@app.route("/calculate", methods=["POST"])
@limiter.limit("10 per minute")  # Example rate limit
def calculate():
    """
    Handle the ROI calculation based on user input.
    """
    try:
        logging.info("Received request to /calculate")
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

        current_price = get_token_price()
        if current_price is None:
            logging.error("Failed to fetch current token price.")
            return jsonify({"error": "Failed to fetch current token price."}), 500

        # Calculate ROI
        tokens_purchased = initial_investment / SEED_ROUND_PRICE
        roi_value = tokens_purchased * current_price

        logging.info(
            f"ROI Calculation - Investment: ${initial_investment}, "
            f"Tokens Purchased: {tokens_purchased}, Current Price: ${current_price}, ROI: ${roi_value}"
        )

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })

    except Exception as e:
        logging.error(f"Error in calculate route: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500


if __name__ == "__main__":
    # Run the Flask application
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ['true', '1', 't']
    app.run(debug=debug_mode)
