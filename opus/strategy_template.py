"""Strategy template. Copy this file to strategies/sNNN.py and change it.

Rules:
  * Every setting goes in PARAMS (no hidden numbers inside signal()).
  * signal(df, **params) returns one value per bar: 1 (long), 0 (flat) or -1 (short).
  * Only use data up to the current bar. Anything that looks into the future
    (for example shift(-1)) is detected by the backtester and rejected.
  * Imports are limited to pandas, numpy and math.
"""
import numpy as np
import pandas as pd

NAME = "EMA trend example"
FAMILY = "trend following"
IDEA = "Long when the fast EMA is above the slow EMA, short when below."
PARAMS = {"fast": 20, "slow": 100}


def signal(df, fast, slow):
    close = df["close"]
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    sig = np.where(ema_fast > ema_slow, 1, np.where(ema_fast < ema_slow, -1, 0))
    return pd.Series(sig, index=df.index)
