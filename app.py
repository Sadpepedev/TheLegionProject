from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# CoinGecko API Function
def get_token_price():
    url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
    params = {
        "contract_addresses": "0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c",
        "vs_currencies": "usd",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("0x675b68aa4d9c2d3bb3f0397048e62e6b7192079c", {}).get("usd", None)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token price: {e}")
        return None

# Flask Routes
@app.route("/")
def home():
    # Fetch the token price
    token_price = get_token_price()
    return render_template("index.html", token_price=token_price)

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        # Get user input
        initial_investment = float(request.json.get("investment", 0))
        round_price = float(request.json.get("round_price", 0))

        # Get the current token price from CoinGecko
        current_price = get_token_price()

        if current_price is None:
            return jsonify({"error": "Failed to fetch current token price."}), 500

        # Calculate ROI
        tokens_purchased = initial_investment / round_price
        roi_value = tokens_purchased * current_price

        return jsonify({
            "initial_investment": initial_investment,
            "current_price": current_price,
            "roi_value": roi_value
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
