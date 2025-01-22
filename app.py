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

# -----------------------------------------------------------
# Existing Token (Fuel) config
# -----------------------------------------------------------
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
TOKEN_CONTRACT_ADDRESS = "0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c"
SEED_ROUND_PRICE = 0.02  # Fixed seed round price in USD

# -----------------------------------------------------------
# Silencio config
# -----------------------------------------------------------
SILENCIO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
SILENCIO_BASE_PRICE = 0.0006  # The base price you provided

# Environment variables for API Key (if required)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# -----------------------------------------------------------
# Cache variables
# -----------------------------------------------------------
# Cache for the existing token (Fuel)
cache = {
    "price": None,
    "timestamp": 0
}
# Cache for Silencio
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


def get_token_price():
    """
    Fetch the current Fuel token price from CoinGecko API (using contract address).
    Implements basic caching to reduce API calls.
    """
    current_time = time.time()
    # If cached price is still valid, return it
    if cache["price"] and (current_time - cache["timestamp"] < CACHE_DURATION):
        logging.info("Using cached token price (Fuel).")
        return cache["price"]

    params = {
        "contract_addresses": TOKEN_CONTRACT_ADDRESS.lower(),
        "vs_currencies": "usd"
    }
    headers = {"accept": "application/json"}
    # Include API key if available
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        logging.info("Fetching Fuel token price from CoinGecko API...")
        response = session.get(COINGECKO_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get(TOKEN_CONTRACT_ADDRESS.lower(), {}).get("usd")
        if price is not None:
            logging.info(f"Fetched token price (Fuel): ${price}")
            cache["price"] = price
            cache["timestamp"] = current_time
            return price
        else:
            logging.error("Fuel token price not found in the API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching token price (Fuel): {e}", exc_info=True)
        return None


def get_silencio_price():
    """
    Fetch the current Silencio price from CoinGecko's simple/price endpoint.
    Implements basic caching to reduce API calls.
    """
    current_time = time.time()
    # If cached price is still valid, return it
    if cache_silencio["price"] and (current_time - cache_silencio["timestamp"] < CACHE_DURATION):
        logging.info("Using cached Silencio price.")
        return cache_silencio["price"]

    params = {
        "ids": "silencio",
        "vs_currencies": "usd"
    }
    headers = {"accept": "application/json"}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    try:
        logging.info("Fetching Silencio price from CoinGecko API...")
        response = session.get(SILENCIO_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        price = data.get("silencio", {}).get("usd")
        if price is not None:
            logging.info(f"Fetched Silencio price: ${price}")
            cache_silencio["price"] = price
            cache_silencio["timestamp"] = current_time
            return price
        else:
            logging.error("Silencio price not found in the API response.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Silencio price: {e}", exc_info=True)
        return None


@app.route("/")
def serve_index():
    """
    Serve the index.html file (Legion ICO Tracker homepage).
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


# ----------------------------------------------------------------
# OPTION A: Explicit routes for each token page
# ----------------------------------------------------------------

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


# ----------------------------------------------------------------
# OPTION B (alternative): A single catch-all route for *any* file
# ----------------------------------------------------------------
# If you prefer a generic approach, comment out the above routes
# and use this instead:
# @app.route("/<path:filename>")
# def serve_any_file(filename):
#     try:
#         return send_from_directory(".", filename)
#     except FileNotFoundError:
#         return "File not found.", 404


@app.route("/calculate", methods=["POST"])
@limiter.limit("10 per minute")  # Example rate limit
def calculate():
    """
    Handle ROI calculation for 'Fuel' token.
    """
    try:
        logging.info("Received request to /calculate (Fuel)")
        data = request.get_json()
        investment_input = data.get("investment")
        round_price = data.get("round_price", SEED_ROUND_PRICE)

        if investment_input is None:
            return jsonify({"error": "Investment input is missing."}), 400

        try:
            initial_investment = float(investment_input)
            if initial_investment <= 0:
                raise ValueError("Investment must be greater than zero.")
        except (TypeError, ValueError) as e:
            return jsonify({"error": str(e)}), 400

        current_price = get_token_price()
        if current_price is None:
            return jsonify({"error": "Failed to fetch current token price (Fuel)."}), 500

        # Calculate ROI
        tokens_purchased = initial_investment / round_price
        roi_value = tokens_purchased * current_price

        logging.info(
            f"[Fuel ROI] Investment: ${initial_investment}, "
            f"Tokens: {tokens_purchased}, Current Price: ${current_price}, ROI: ${roi_value}"
        )

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })

    except Exception as e:
        logging.error(f"Error in /calculate route (Fuel): {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred in /calculate (Fuel)."}), 500


@app.route("/calculate_silencio", methods=["POST"])
@limiter.limit("10 per minute")  # Example rate limit
def calculate_silencio():
    """
    Handle ROI calculation for Silencio (base price is 0.0006).
    """
    try:
        logging.info("Received request to /calculate_silencio (Silencio)")
        data = request.get_json()
        investment_input = data.get("investment")

        if investment_input is None:
            return jsonify({"error": "Investment input is missing."}), 400

        try:
            initial_investment = float(investment_input)
            if initial_investment <= 0:
                raise ValueError("Investment must be greater than zero.")
        except (TypeError, ValueError) as e:
            return jsonify({"error": str(e)}), 400

        current_price = get_silencio_price()
        if current_price is None:
            return jsonify({"error": "Failed to fetch Silencio token price."}), 500

        # Calculate ROI based on Silencio base price (0.0006)
        tokens_purchased = initial_investment / SILENCIO_BASE_PRICE
        roi_value = tokens_purchased * current_price

        logging.info(
            f"[Silencio ROI] Investment: ${initial_investment}, "
            f"Tokens: {tokens_purchased}, Current Price: ${current_price}, ROI: ${roi_value}"
        )

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })

    except Exception as e:
        logging.error(f"Error in /calculate_silencio route (Silencio): {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred in /calculate_silencio."}), 500


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ['true', '1', 't']
    app.run(debug=debug_mode)
