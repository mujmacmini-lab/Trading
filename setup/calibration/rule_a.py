"""Calibration rule A: long when the 90/180/360-candle momentum votes are net positive."""
import numpy as np
import pandas as pd

NAME = "Calibration A: momentum vote"
FAMILY = "calibration"
IDEA = "Long when the sum of the signs of the 90-, 180- and 360-candle returns is above zero, otherwise flat."
PARAMS = {"lookbacks": (90, 180, 360)}


def signal(df, lookbacks):
    close = df["close"]
    votes = pd.Series(0.0, index=df.index)
    for n in lookbacks:
        votes = votes + np.sign(close.pct_change(n)).fillna(0)  # missing history counts as 0
    return (votes > 0).astype(int)
