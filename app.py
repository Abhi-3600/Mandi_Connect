from flask import Flask, request, jsonify
from cachetools import TTLCache, cached
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

DATA_GOV_KEY = os.environ.get("DATA_GOV_API_KEY")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# Cache for 15 minutes
cache = TTLCache(maxsize=200, ttl=60 * 15)

def dict_to_tuple(d):
    return tuple(sorted(d.items()))

@cached(cache, key=lambda params: dict_to_tuple(params))
def fetch_from_datagov(params):
    params.update({"api-key": DATA_GOV_KEY, "format": "json", "limit": 5000})
    resp = requests.get(BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

@app.route("/")
def home():
    return {
        "message": "✅ Farmer Market API is live on Railway!",
        "usage": "Try /prices?state=Maharashtra&commodity=Onion"
    }

@app.route("/prices")
def prices():
    params = {}

    # ✅ Correct lowercase field names for filters
    state = request.args.get("state")
    if state:
        params["filters[state]"] = state

    commodity = request.args.get("commodity")
    if commodity:
        params["filters[commodity]"] = commodity

    market = request.args.get("market")
    if market:
        params["filters[market]"] = market

    arrival_date = request.args.get("arrival_date")
    if arrival_date:
        params["filters[arrival_date]"] = arrival_date

    try:
        data = fetch_from_datagov(params)
        records = data.get("records", [])
        normalized = []

        # ✅ Match JSON key names (all lowercase)
        for r in records:
            normalized.append({
                "state": r.get("state"),
                "district": r.get("district"),
                "market": r.get("market"),
                "commodity": r.get("commodity"),
                "variety": r.get("variety"),
                "arrival_date": r.get("arrival_date"),
                "min_price": r.get("min_price"),
                "max_price": r.get("max_price"),
                "modal_price": r.get("modal_price"),
            })

        if not normalized:
            return jsonify({"message": "No records found for these filters.", "records": []})

        return jsonify({"records": normalized})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
