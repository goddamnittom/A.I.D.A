"""
Crypto monitoring tool using ccxt (or fallback to public APIs).
Starts in monitor-only mode.
"""

import ccxt
from datetime import datetime

def crypto_price(args: dict, config: dict = None) -> str:
    """
    Get current prices.
    args: {"symbols": ["BTC", "ETH"], "vs_currency": "USD"}
    """
    symbols = args.get("symbols", ["BTC", "ETH"])
    vs = args.get("vs_currency", "USD").lower()
    
    monitor_only = config.get("monitor_only_crypto", True) if config else True
    
    try:
        exchange = ccxt.binance()  # or kraken, coinbase, etc. No API key needed for public ticker
        results = []
        
        for sym in symbols:
            pair = f"{sym.upper()}/{vs.upper()}"
            try:
                ticker = exchange.fetch_ticker(pair)
                price = ticker.get("last") or ticker.get("close")
                change = ticker.get("percentage", 0)
                results.append(f"{sym}: ${price:,.2f} ({change:+.2f}%)")
            except Exception as e:
                results.append(f"{sym}: Error - {str(e)[:60]}")
        
        output = " | ".join(results)
        
        if not monitor_only:
            output += " [TRADING ENABLED - USE WITH CAUTION]"
        
        return output
        
    except Exception as e:
        return f"Error fetching crypto prices: {str(e)}"