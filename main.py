import os, yaml, time, pandas as pd
from binance.client import Client
from utils.signals import check_signal
from utils.risk import dca_logic, check_take_profit, check_stop_loss
from utils.telegram import send_alert
from utils.pnl import update_pnl, report_pnl

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Prefer environment variables (GitHub Secrets) if available
api_key = os.getenv("BINANCE_API_KEY", config["binance"]["api_key"])
api_secret = os.getenv("BINANCE_SECRET", config["binance"]["api_secret"])
telegram_token = os.getenv("TELEGRAM_TOKEN", config["telegram"]["token"])
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", config["telegram"]["chat_id"])

client = Client(api_key, api_secret)

capital = 1000
mode = config.get("mode", "paper")
track_pnl = config.get("pnl_tracking", False)

# Load halal universe
halal_coins = pd.read_csv("halal_universe.csv")["symbol"].tolist()

open_trades, pnl_log = [], []

def place_order(symbol, qty, side="BUY"):
    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    if mode == "paper":
        send_alert(f"[PAPER] {side} {symbol}, qty={qty}, price={price}")
        return {"fills":[{"price":price}]}
    else:
        if side == "BUY":
            order = client.order_market_buy(symbol=symbol, quantity=qty)
        else:
            order = client.order_market_sell(symbol=symbol, quantity=qty)
        send_alert(f"{side} {symbol}, qty={qty}")
        return order

while True:
    # Entry logic
    if len(open_trades) < config["max_open_trades"]:
        for symbol in halal_coins:
            if check_signal(client, symbol, config):
                current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
                qty = config["allocation_per_trade"] / current_price
                order = place_order(symbol, qty, "BUY")
                trade = {
                    "symbol": symbol,
                    "qty": qty,
                    "entry": float(order['fills'][0]['price']),
                    "last_buy": float(order['fills'][0]['price']),
                    "dca_count": 0
                }
                open_trades.append(trade)
                if track_pnl: pnl_log.append(trade)
                if len(open_trades) >= config["max_open_trades"]:
                    break

    # Manage trades
    for trade in open_trades[:]:
        if check_take_profit(client, trade, place_order, config):
            send_alert(f"✅ TP hit: {trade['symbol']} +1.15%")
            open_trades.remove(trade)
        elif check_stop_loss(client, trade, place_order, config):
            send_alert(f"❌ SL hit: {trade['symbol']} −6%")
            open_trades.remove(trade)
        else:
            dca_logic(client, trade, place_order, config)

        if track_pnl:
            update_pnl(client, trade, pnl_log)

    if track_pnl:
        report_pnl(pnl_log)

    time.sleep(60)  # run every minute
