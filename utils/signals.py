import pandas as pd

def get_candles(okx_request, symbol, interval="1h", limit=100):
    data = okx_request("GET", "/api/v5/market/candles", {
        "instId": symbol,
        "bar": interval,
        "limit": str(limit)
    })
    candles = data.get("data", [])
    if not candles:
        return pd.DataFrame()  # return empty DataFrame safely

    df = pd.DataFrame(candles, columns=[
        "ts","open","high","low","close","vol","volCcy","volCcyQuote","confirm"
    ])
    df = df.astype({"open":float,"high":float,"low":float,"close":float,"vol":float})
    df = df.iloc[::-1].reset_index(drop=True)  # reverse to chronological order
    return df

def check_signal(okx_request, symbol, config):
    df = get_candles(okx_request, symbol, interval="1h", limit=100)

    if df.empty or len(df) < 2:
        # No data, skip signal
        return False

    # Example: EMA crossover
    df["ema_fast"] = df["close"].ewm(span=9).mean()
    df["ema_slow"] = df["close"].ewm(span=21).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    if prev["ema_fast"] <= prev["ema_slow"] and latest["ema_fast"] > latest["ema_slow"]:
        return True
    return False
