def check_signal(client, symbol, config):
    klines = client.get_klines(symbol=symbol, interval="1h", limit=100)
    closes = [float(k[4]) for k in klines]
    signals_cfg = config["signals"]

    # EMA crossover
    if signals_cfg["ema"]["enabled"]:
        ema_short = sum(closes[-signals_cfg["ema"]["short_period"]:]) / signals_cfg["ema"]["short_period"]
        ema_long = sum(closes[-signals_cfg["ema"]["long_period"]:]) / signals_cfg["ema"]["long_period"]
        if ema_short <= ema_long:
            return False

    # RSI filter
    if signals_cfg["rsi"]["enabled"]:
        gains = [closes[i+1]-closes[i] for i in range(len(closes)-1) if closes[i+1]>closes[i]]
        losses = [closes[i]-closes[i+1] for i in range(len(closes)-1) if closes[i+1]<closes[i]]
        avg_gain = sum(gains[-signals_cfg["rsi"]["period"]:]) / signals_cfg["rsi"]["period"] if gains else 0
        avg_loss = sum(losses[-signals_cfg["rsi"]["period"]:]) / signals_cfg["rsi"]["period"] if losses else 1
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        if rsi > signals_cfg["rsi"]["overbought"]:
            return False

    # MACD confirmation
    if signals_cfg["macd"]["enabled"]:
        ema_fast = sum(closes[-signals_cfg["macd"]["fast_period"]:]) / signals_cfg["macd"]["fast_period"]
        ema_slow = sum(closes[-signals_cfg["macd"]["slow_period"]:]) / signals_cfg["macd"]["slow_period"]
        macd_line = ema_fast - ema_slow
        signal_line = sum(closes[-signals_cfg["macd"]["signal_period"]:]) / signals_cfg["macd"]["signal_period"]
        if macd_line <= signal_line:
            return False

    # Volume spike
    if signals_cfg["volume"]["enabled"]:
        volumes = [float(k[5]) for k in klines]
        avg_vol = sum(volumes[-signals_cfg["volume"]["lookback"]:]) / signals_cfg["volume"]["lookback"]
        if volumes[-1] < avg_vol:
            return False

    return True
