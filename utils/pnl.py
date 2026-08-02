from utils.telegram import send_alert

def update_pnl(client, trade, pnl_log):
    current_price = float(client.get_symbol_ticker(symbol=trade['symbol'])['price'])
    entry = trade['entry']
    qty = trade['qty']
    unrealized = (current_price - entry) * qty
    trade['unrealized'] = unrealized

def report_pnl(pnl_log):
    total_unrealized = sum(t.get('unrealized', 0) for t in pnl_log)
    msg = f"[PAPER] Current unrealized PnL: {total_unrealized:.2f} USDT"
    send_alert(msg)
