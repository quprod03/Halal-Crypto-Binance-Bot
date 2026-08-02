def dca_logic(client, trade, place_order, config):
    current_price = float(client.get_symbol_ticker(symbol=trade['symbol'])['price'])
    last_buy_price = trade.get("last_buy", trade["entry"])
    if current_price < last_buy_price * (1 - config["dca_trigger_percent"]) and trade["dca_count"] < config["max_dca_per_trade"]:
        qty = trade['qty'] * 0.5
        order = place_order(trade['symbol'], qty, "BUY")
        trade["dca_count"] += 1
        trade["last_buy"] = float(order['fills'][0]['price'])

def check_take_profit(client, trade, place_order, config):
    current_price = float(client.get_symbol_ticker(symbol=trade['symbol'])['price'])
    if current_price >= trade['entry'] * (1 + config["take_profit_percent"]):
        place_order(trade['symbol'], trade['qty'], "SELL")
        return True
    return False

def check_stop_loss(client, trade, place_order, config):
    current_price = float(client.get_symbol_ticker(symbol=trade['symbol'])['price'])
    if current_price <= trade['entry'] * (1 - config["stop_loss_percent"]):
        place_order(trade['symbol'], trade['qty'], "SELL")
        return True
    return False
