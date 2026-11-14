"""Download Bybit BTCUSDT perpetual 4-hour candles and hide the exam year.

Usage (run from anywhere):
    python setup/download.py

What it does:
  1. Pages through Bybit v5 /market/kline (category=linear, interval=240, 1000 per call)
     from the candle opening 2020-04-01 00:00 UTC up to and including the candle
     opening 2026-11-01 00:00 UTC (14,431 candles).
  2. Checks there are no gaps and no duplicates.
  3. Writes  fable/data/BTCUSDT_4h_insample.csv  (ts before 2025-11-01, 12,240 candles)
     and     hidden/BTCUSDT_4h_full.csv          (all 14,431 candles).
     If opus/ already exists (it is a copy of fable/), its in-sample file is written too.

Nothing raw is saved to disk: candles are held in memory and only the files above are written.
Bybit refuses its API to some countries (HTTP 403); run this from a location Bybit serves.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

URL = "https://api.bybit.com/v5/market/kline"
SYMBOL = "BTCUSDT"
INTERVAL_MIN = 240
STEP_MS = INTERVAL_MIN * 60 * 1000
LIMIT = 1000

FIRST = pd.Timestamp("2020-04-01 00:00", tz="UTC")
LAST = pd.Timestamp("2026-11-01 00:00", tz="UTC")
EXAM_START = pd.Timestamp("2025-11-01 00:00", tz="UTC")
N_FULL = 14431
N_INSAMPLE = 12240

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSAMPLE_NAME = "BTCUSDT_4h_insample.csv"
FULL_PATH = os.path.join(ROOT, "hidden", "BTCUSDT_4h_full.csv")


def to_ms(ts):
    return int(ts.timestamp() * 1000)


def fetch_page(start_ms, end_ms):
    """One API call: candles with start_ms <= open time <= end_ms (at most LIMIT)."""
    query = urllib.parse.urlencode({
        "category": "linear", "symbol": SYMBOL, "interval": INTERVAL_MIN,
        "start": start_ms, "end": end_ms, "limit": LIMIT,
    })
    req = urllib.request.Request(f"{URL}?{query}", headers={"User-Agent": "python-urllib"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.load(resp)
            if body.get("retCode") != 0:
                raise RuntimeError(f"Bybit error {body.get('retCode')}: {body.get('retMsg')}")
            return body["result"]["list"]
        except urllib.error.HTTPError as e:
            if e.code == 403:
                sys.exit("Bybit refused the request (HTTP 403): its API is not available from this "
                         "location. Run this script from a location Bybit serves.")
            last_error = e
        except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
            last_error = e
        time.sleep(2 ** attempt)
    raise RuntimeError(f"giving up after 5 attempts: {last_error}")


def download():
    rows = []
    cursor, end = to_ms(FIRST), to_ms(LAST)
    while cursor <= end:
        page_end = min(cursor + (LIMIT - 1) * STEP_MS, end)
        page = fetch_page(cursor, page_end)
        if not page:
            raise RuntimeError(f"empty page starting at {pd.to_datetime(cursor, unit='ms', utc=True)}")
        rows.extend(page)
        print(f"  {len(rows):>6} candles", end="\r", flush=True)
        cursor = page_end + STEP_MS
        time.sleep(0.1)
    print()
    # Bybit row: [startTime, open, high, low, close, volume, turnover], newest first within a page
    df = pd.DataFrame([r[:6] for r in rows], columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df.sort_values("ts", kind="stable").reset_index(drop=True)


def check(df):
    """Fail loudly on duplicates, gaps or a wrong range."""
    dupes = int(df["ts"].duplicated().sum())
    if dupes:
        raise SystemExit(f"CHECK FAILED: {dupes} duplicate candles")
    expected = pd.date_range(FIRST, LAST, freq=f"{INTERVAL_MIN}min")
    missing = expected.difference(pd.DatetimeIndex(df["ts"]))
    if len(missing):
        raise SystemExit(f"CHECK FAILED: {len(missing)} missing candles, first gap at {missing[0]}")
    extra = pd.DatetimeIndex(df["ts"]).difference(expected)
    if len(extra):
        raise SystemExit(f"CHECK FAILED: {len(extra)} unexpected candles, first at {extra[0]}")
    if len(df) != N_FULL:
        raise SystemExit(f"CHECK FAILED: {len(df)} candles, expected {N_FULL}")
    if df[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise SystemExit("CHECK FAILED: missing values")
    print(f"  no gaps, no duplicates: {len(df)} candles from {df['ts'].iloc[0]} to {df['ts'].iloc[-1]}")


def write(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")  # header: ts,open,high,low,close,volume
    print(f"  wrote {len(df):>6} candles  {df['ts'].iloc[0]} -> {df['ts'].iloc[-1]}  {os.path.relpath(path, ROOT)}")


def main():
    print("Downloading Bybit BTCUSDT perpetual 4h candles ...")
    df = download()
    print("Checking ...")
    check(df)
    insample = df[df["ts"] < EXAM_START]
    if len(insample) != N_INSAMPLE:
        raise SystemExit(f"CHECK FAILED: {len(insample)} in-sample candles, expected {N_INSAMPLE}")
    print("Saving ...")
    write(insample, os.path.join(ROOT, "fable", "data", INSAMPLE_NAME))
    if os.path.isdir(os.path.join(ROOT, "opus")):
        write(insample, os.path.join(ROOT, "opus", "data", INSAMPLE_NAME))
    write(df, FULL_PATH)


if __name__ == "__main__":
    main()
