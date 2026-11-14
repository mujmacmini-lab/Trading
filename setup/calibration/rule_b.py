"""Calibration rule B: EMA 200 with a 1% band, holding the previous position inside the band."""
import numpy as np
import pandas as pd

NAME = "Calibration B: EMA 200 band"
FAMILY = "calibration"
IDEA = "Long when close > EMA200 * 1.01, short when close < EMA200 * 0.99, otherwise keep the previous position."
PARAMS = {"span": 200, "band": 0.01}


def signal(df, span, band):
    close = df["close"]
    ema = close.ewm(span=span, adjust=False).mean()
    raw = pd.Series(np.nan, index=df.index)
    raw[close > ema * (1 + band)] = 1.0
    raw[close < ema * (1 - band)] = -1.0
    return raw.ffill().fillna(0)  # keep previous position, starting flat
