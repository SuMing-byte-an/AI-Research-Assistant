#!/usr/bin/env python3
"""
Standalone Python version of the Dify Code Execution node.

Fetches HK stock daily data from Tushare API, computes MA5,
and generates a brief technical analysis text for LLM consumption.

This is the Python equivalent of the JavaScript code node in the Dify workflow.
It can be used independently for testing or as a reference for implementation.

Usage:
    python quant_compute.py --symbol 00700.HK --days 5

Environment:
    TUSHARE_TOKEN must be set in .env or environment variable.
"""

import json
import os
import argparse
import sys

try:
    import requests
except ImportError:
    # Fallback: use urllib if requests is not available
    from urllib.request import Request, urlopen
    from urllib.error import URLError

    def _post(url, data, timeout=30):
        req = Request(url, data=data.encode("utf-8"), headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    requests = None


def fetch_tushare_hk_daily(symbol, token, days=5):
    """Fetch HK stock daily data from Tushare Pro API."""
    payload = {
        "api_name": "hk_daily",
        "token": token,
        "params": {"ts_code": symbol},
        "fields": "ts_code,trade_date,open,high,low,close,vol",
    }

    if requests:
        resp = requests.post(
            "http://api.tushare.pro",
            json=payload,
            timeout=30,
        )
        data = resp.json()
    else:
        data = _post("http://api.tushare.pro", json.dumps(payload))

    if data.get("code") != 0:
        return None, f"Tushare API error: {data.get('msg', 'unknown')}"

    items = data.get("data", {}).get("items", [])
    if not items:
        return None, "No data returned from Tushare"

    # Tushare data format: ["ts_code", "trade_date", "open", "high", "low", "close", "vol"]
    # Indices:             0          1            2      3      4      5       6
    prices = []
    for i in range(min(days, len(items))):
        prices.append({
            "date": items[i][1],
            "close": float(items[i][5]),
            "vol": float(items[i][6]),
        })

    return prices, None


def compute_ma5(prices):
    """Compute 5-day moving average and generate analysis text."""
    if len(prices) == 0:
        return "未能获取到有效的行情数据"

    closes = [p["close"] for p in prices]
    ma5 = sum(closes) / len(closes)
    latest_close = prices[0]["close"]

    analysis = f"量化数据提取成功：\n最新收盘价: {latest_close}\n5日均线 (MA5): {ma5:.2f}\n"
    if latest_close > ma5:
        analysis += "技术面特征: 当前收盘价已站上5日均线，呈现短期多头排列。"
    else:
        analysis += "技术面特征: 当前收盘价低于5日均线，呈现短期空头排列。"

    return analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch HK stock data and compute MA5")
    parser.add_argument("--symbol", default="00700.HK", help="HK stock code (e.g. 00700.HK)")
    parser.add_argument("--days", type=int, default=5, help="Number of trading days to analyze")
    parser.add_argument("--token", default=None, help="Tushare token (or set TUSHARE_TOKEN env)")
    args = parser.parse_args()

    token = args.token or os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        print("Error: TUSHARE_TOKEN not set. Use --token or set TUSHARE_TOKEN environment variable.")
        print("Get your token at: https://tushare.pro/register")
        sys.exit(1)

    prices, error = fetch_tushare_hk_daily(args.symbol, token, args.days)
    if error:
        print(f"Error: {error}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"HK Stock: {args.symbol}")
    print(f"Recent {len(prices)} trading days:")
    print(f"{'='*60}")
    for p in prices:
        print(f"  {p['date']}  Close: {p['close']:.2f}  Vol: {p['vol']:.0f}")

    result = compute_ma5(prices)
    print(f"\n{result}")
