import pandas as pd

def rma(series, length):
    """TradingView RMA (Wilder smoothing)"""
    alpha = 1 / length
    return series.ewm(alpha=alpha, adjust=False).mean()

def rsi_tv(close, length=31):
    """TradingView RSI — %100 uyumlu"""
    delta = close.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = rma(gain, length)
    avg_loss = rma(loss, length)

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi
