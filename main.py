import os, yaml, time, pandas as pd
from okx.Account import Account
from okx.Market import Market
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

# Initialize OKX clients (spot trading)
accountAPI = Account(api_key, api_secret, passphrase, False, "0")
marketAPI = Market(api_key, api_secret, passphrase, False, "0")

capital = 1000
mode = config.get("mode", "paper")
track_pnl = config.get("pnl_tracking", False)

# Load halal universe (symbols must be in OKX format, e.g. BTC-USDT)
halal_coins = pd.read_csv("halal_universe.csv")["symbol"].tolist()

open_trades, pnl_log = [], []

def get_price(symbol):
    ticker = marketAPI.get_ticker(symbol)
    return float(ticker['data'][0]['last'])

def place_order(symbol, qty, side="buy"):
    price = get_price(symbol)
    if mode == "paper":
        send_alert(f"[PAPER] {side.upper()} {symbol}, qty={qty}, price={price}")
        return {"price": price}
    else:
        order = accountAPI.place_order(
            instId=symbol,
            tdMode="cash",
            side=side,
            ordType="market",
            sz=str(qty)
        )
        send_alert(f"{side.upper()} {symbol}, qty={qty}")
        return order

while True:
    # Entry logic
    if len(open_trades) < config["max_open_trades"]:
        for symbol in halal_coins:
            if check_signal(marketAPI, symbol, config):
                current_price = get_price(symbol)
                qty = config["allocation_per_trade"] / current_price
                order = place_order(symbol, qty, "buy")
                trade = {
                    "symbol": symbol,
                    "qty": qty,
                    "entry": order.get("price", current_price),
                    "last_buy": order.get("price", current_price),
                    "dca_count": 0
                }
                open_trades.append(trade)
                if track_pnl: pnl_log.append(trade)
                if len(open_trades) >= config["max_open_trades"]:
                    break

    # Manage trades
    for trade in open_trades[:]:
        if check_take_profit(marketAPI, trade, place_order, config):
            send_alert(f"✅ TP hit: {trade['symbol']} +{config['take_profit_percent']*100:.2f}%")
            open_trades.remove(trade)
        elif check_stop_loss(marketAPI, trade, place_order, config):
            send_alert(f"❌ SL hit: {trade['symbol']} −{config['stop_loss_percent']*100:.2f}%")
            open_trades.remove(trade)
        else:
            dca_logic(marketAPI, trade, place_order, config)

        if track_pnl:
            update_pnl(marketAPI, trade, pnl_log)

    if track_pnl:
        report
