import os, yaml, time, json, hmac, hashlib, base64, requests, pandas as pd
from utils.signals import check_signal
from utils.risk import dca_logic, check_take_profit, check_stop_loss
from utils.telegram import send_alert
from utils.pnl import update_pnl, report_pnl

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Prefer environment variables (GitHub Secrets) if available
api_key = os.getenv("OKX_API_KEY", config["okx"]["api_key"])
api_secret = os.getenv("OKX_API_SECRET", config["okx"]["api_secret"])
passphrase = os.getenv("OKX_PASSPHRASE", config["okx"]["passphrase"])

base_url = "https://www.okx.com"

def okx_request(method, endpoint, params=None):
    ts = str(time.time())
    body = "" if params is None else json.dumps(params)
    message = ts + method.upper() + endpoint + body
    sign = base64.b64encode(
        hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()

    headers = {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }

    resp = requests.request(method, base_url + endpoint, headers=headers, data=body)
    return resp.json()

capital = 1000
mode = config.get("mode", "paper")
track_pnl = config.get("pnl_tracking", False)

# Load halal universe (symbols must be in OKX format, e.g. BTC-USDT)
halal_coins = pd.read_csv("halal_universe.csv")["symbol"].tolist()

open_trades, pnl_log = [], []

def get_price(symbol):
    data = okx_request("GET", "/api/v5/market/ticker", {"instId": symbol})
    return float(data["data"][0]["last"])

def place_order(symbol, qty, side="buy"):
    price = get_price(symbol)
    if mode == "paper":
        send_alert(f"[PAPER] {side.upper()} {symbol}, qty={qty}, price={price}")
        return {"price": price}
    else:
