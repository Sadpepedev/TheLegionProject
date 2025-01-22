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
    handlers=[logging.StreamHandler()]  # Logs to stdout
)

# Initialize Limiter for rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]  # Example global limits
)
limiter.init_app(app)

# ----------------------------------------------------------------------------
# FUEL SETTINGS (unchanged from your original)
# ----------------------------------------------------------------------------
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
TOKEN_CONTRACT_ADDRESS = "0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c"
SEED_ROUND_PRICE = 0.02  # Fuel base price

# ----------------------------------------------------------------------------
# SILENCIO SETTINGS (new)
# ----------------------------------------------------------------------------
SILENCIO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
SILENCIO_BASE_PRICE = 0.0006  # The base price you provided

# Environment variable for optional API key
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# ----------------------------------------------------------------------------
# CACHING
# ----------------------------------------------------------------------------
cache_fuel = {
    "price": None,
    "timestamp": 0
}
cache_silencio = {
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

# ----------------------------------------------------------------------------
# Fuel Price Fetch (unchanged)
# ----------------------------------------------------------------------------
def get_fuel_price():
    """
    Fetch the current Fuel token price from CoinGecko API (using contract address).
    Implements basic caching to reduce API calls.
    """
    current_time = time.time()
    if cache_fuel["price"] and (current_time - cache_fuel["timestamp"] < CACHE_DURATION):
        logging.info("Using cached FUEL price.")
        return cache_fuel["price"]

    params = {
        "contract_addresses": TOKEN_CONTRACT_ADDRESS.lower(),
        "vs_currencies": "usd"
    }
    headers = {"accept": "application/json"}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        logging.info("Fetching FUEL token price from CoinGecko API...")
        response = session.get(COINGECKO_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get(TOKEN_CONTRACT_ADDRESS.lower(), {}).get("usd")
        if price is not None:
            cache_fuel["price"] = price
            cache_fuel["timestamp"] = current_time
            logging.info(f"Fetched FUEL price: ${price}")
            return price
        else:
            logging.error("FUEL price not found in API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching FUEL price: {e}", exc_info=True)
        return None

# ----------------------------------------------------------------------------
# Silencio Price Fetch (new)
# ----------------------------------------------------------------------------
def get_silencio_price():
    """
    Fetch the current Silencio price from CoinGecko's simple/price endpoint.
    Implements basic caching to reduce API calls.
    """
    current_time = time.time()
    if cache_silencio["price"] and (current_time - cache_silencio["timestamp"] < CACHE_DURATION):
        logging.info("Using cached SILENCIO price.")
        return cache_silencio["price"]

    params = {
        "ids": "silencio",
        "vs_currencies": "usd"
    }
    headers = {"accept": "application/json"}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        logging.info("Fetching SILENCIO price from CoinGecko API...")
        response = session.get(SILENCIO_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get("silencio", {}).get("usd")
        if price is not None:
            cache_silencio["price"] = price
            cache_silencio["timestamp"] = current_time
            logging.info(f"Fetched SILENCIO price: ${price}")
            return price
        else:
            logging.error("SILENCIO price not found in API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching SILENCIO price: {e}", exc_info=True)
        return None

# ----------------------------------------------------------------------------
# Serve index.html
# ----------------------------------------------------------------------------
@app.route("/")
def serve_index():
    try:
        logging.info("Serving index.html from the root directory.")
        return send_from_directory(".", "index.html")
    except FileNotFoundError:
        return "index.html not found.", 404
    except Exception as e:
        logging.error(f"Error serving index.html: {e}", exc_info=True)
        return "An error occurred while loading the page.", 500

# ----------------------------------------------------------------------------
# Serve other pages (unchanged)
# ----------------------------------------------------------------------------
@app.route("/fuel.html")
def serve_fuel():
    try:
        return send_from_directory(".", "fuel.html")
    except FileNotFoundError:
        return "fuel.html not found.", 404

@app.route("/almanak.html")
def serve_almanak():
    try:
        return send_from_directory(".", "almanak.html")
    except FileNotFoundError:
        return "almanak.html not found.", 404

@app.route("/pulse.html")
def serve_pulse():
    try:
        return send_from_directory(".", "pulse.html")
    except FileNotFoundError:
        return "pulse.html not found.", 404

@app.route("/silencio.html")
def serve_silencio():
    try:
        return send_from_directory(".", "silencio.html")
    except FileNotFoundError:
        return "silencio.html not found.", 404

@app.route("/enclave.html")
def serve_enclave():
    try:
        return send_from_directory(".", "enclave.html")
    except FileNotFoundError:
        return "enclave.html not found.", 404

@app.route("/corn.html")
def serve_corn():
    try:
        return send_from_directory(".", "corn.html")
    except FileNotFoundError:
        return "corn.html not found.", 404

@app.route("/giza.html")
def serve_giza():
    try:
        return send_from_directory(".", "giza.html")
    except FileNotFoundError:
        return "giza.html not found.", 404

# ----------------------------------------------------------------------------
# Existing /calculate route for Fuel (unchanged)
# ----------------------------------------------------------------------------
@app.route("/calculate", methods=["POST"])
@limiter.limit("10 per minute")
def calculate_fuel():
    """
    Handle ROI calculation for the 'Fuel' token.
    """
    try:
        data = request.get_json()
        investment_input = data.get("investment")
        round_price = data.get("round_price", SEED_ROUND_PRICE)

        if investment_input is None:
            return jsonify({"error": "Investment input is missing."}), 400

        initial_investment = float(investment_input)
        if initial_investment <= 0:
            raise ValueError("Investment must be greater than zero.")

        current_price = get_fuel_price()
        if current_price is None:
            return jsonify({"error": "Failed to fetch Fuel price."}), 500

        tokens_purchased = initial_investment / round_price
        roi_value = tokens_purchased * current_price

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })

    except Exception as e:
        logging.error(f"Error in /calculate (Fuel): {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred in /calculate (Fuel)."}), 500

# ----------------------------------------------------------------------------
# New /calculate_silencio route
# ----------------------------------------------------------------------------
@app.route("/calculate_silencio", methods=["POST"])
@limiter.limit("10 per minute")
def calculate_silencio():
    """
    Handle ROI calculation for Silencio (base = 0.0006).
    """
    try:
        data = request.get_json()
        investment_input = data.get("investment")

        if investment_input is None:
            return jsonify({"error": "Investment input is missing."}), 400

        initial_investment = float(investment_input)
        if initial_investment <= 0:
            raise ValueError("Investment must be greater than zero.")

        current_price = get_silencio_price()
        if current_price is None:
            return jsonify({"error": "Failed to fetch Silencio price."}), 500

        # ROI calculation
        tokens_purchased = initial_investment / SILENCIO_BASE_PRICE
        roi_value = tokens_purchased * current_price

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })

    except Exception as e:
        logging.error(f"Error in /calculate_silencio (Silencio): {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred in /calculate_silencio."}), 500


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ['true', '1', 't']
    app.run(debug=debug_mode)
