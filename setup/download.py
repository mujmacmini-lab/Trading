"""Download Binance BTCUSDT perpetual 4-hour candles and hide the exam year.

Usage (run from anywhere):
    python setup/download.py

What it does:
  1. Downloads Binance USD-M futures BTCUSDT 4h candles from Binance's public data archive
     (data.binance.vision: one zip per month, plus one daily zip for the final candle),
     verifying each zip against Binance's published SHA-256 checksum.
     Range: the candle opening 2020-04-01 00:00 UTC up to and including the candle
     opening 2026-11-01 00:00 UTC (14,431 candles).
  2. Checks there are no gaps and no duplicates.
  3. Writes  fable/data/BTCUSDT_4h_insample.csv  (ts before 2025-11-01, 12,240 candles)
     and     hidden/BTCUSDT_4h_full.csv          (all 14,431 candles).
     If opus/ already exists (it is a copy of fable/), its in-sample file is written too.

Nothing raw is saved to disk: the zips are read in memory and only the files above are written.
"""
import hashlib
import io
import os
import time
import urllib.error
import urllib.request
import zipfile

import pandas as pd

BASE = "https://data.binance.vision/data/futures/um"
SYMBOL = "BTCUSDT"
INTERVAL = "4h"

FIRST = pd.Timestamp("2020-04-01 00:00", tz="UTC")
LAST = pd.Timestamp("2026-11-01 00:00", tz="UTC")
EXAM_START = pd.Timestamp("2025-11-01 00:00", tz="UTC")
N_FULL = 14431
N_INSAMPLE = 12240

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSAMPLE_NAME = "BTCUSDT_4h_insample.csv"
FULL_PATH = os.path.join(ROOT, "hidden", "BTCUSDT_4h_full.csv")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"giving up on {url} after 5 attempts: {last_error}")


def fetch_zip(kind, period):
    """kind is 'monthly' (period '2020-04') or 'daily' (period '2026-11-01'). Returns candle rows."""
    name = f"{SYMBOL}-{INTERVAL}-{period}.zip"
    url = f"{BASE}/{kind}/klines/{SYMBOL}/{INTERVAL}/{name}"
    blob = get(url)
    expected_sha = get(url + ".CHECKSUM").decode().split()[0]
    if hashlib.sha256(blob).hexdigest() != expected_sha:
        raise RuntimeError(f"checksum mismatch for {name}")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        with z.open(z.namelist()[0]) as f:
            raw = pd.read_csv(f, header=None, dtype=str)
    # Binance row: open_time, open, high, low, close, volume, close_time, ... (some files have a header row)
    raw = raw[raw[0].str.isdigit()].iloc[:, :6]
    raw.columns = ["ts", "open", "high", "low", "close", "volume"]
    return raw


def download():
    parts = []
    months = pd.period_range(FIRST, LAST - pd.Timedelta(days=1), freq="M")
    for i, month in enumerate(months, 1):
        parts.append(fetch_zip("monthly", str(month)))
        print(f"  {i}/{len(months)} months", end="\r", flush=True)
    print()
    parts.append(fetch_zip("daily", LAST.strftime("%Y-%m-%d")))  # the final candle, 2026-11-01 00:00
    df = pd.concat(parts, ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df = df[(df["ts"] >= FIRST) & (df["ts"] <= LAST)]
    return df.sort_values("ts", kind="stable").reset_index(drop=True)


def check(df):
    """Fail loudly on duplicates, gaps or a wrong range."""
    dupes = int(df["ts"].duplicated().sum())
    if dupes:
        raise SystemExit(f"CHECK FAILED: {dupes} duplicate candles")
    expected = pd.date_range(FIRST, LAST, freq="4h")
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
    print("Downloading Binance BTCUSDT perpetual 4h candles ...")
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
