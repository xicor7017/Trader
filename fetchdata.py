import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

def fetch_price_data(symbols: Optional[List[str]] = None,
                     period: int = 30,  # period in minutes
                     interval: str = "1m") -> Dict[str, pd.DataFrame]:
    
    data: Dict[str, pd.DataFrame] = {}

    # Bulk download for all symbols
    try:
        df = yf.download(
            tickers=symbols,
            period="1d",  # fetch at least one day of data to cover intraday history
            interval=interval,
            auto_adjust=False,
            group_by="ticker",
            threads=True
        )
    except Exception as e:
        print(f"[ERROR] Bulk download failed: {e}")
        return None

    # Parse period string (e.g., '30m' -> 30)
    minutes = period
    prices_data = {}
    for symbol in symbols:
        close_prices = np.array(df[symbol]['Close'].values)
        if len(close_prices) > minutes:
            prices_data[symbol] = close_prices[-minutes:]

    return prices_data


if __name__ == "__main__":
    from parameters import Parameters
    symbols = Parameters.symbols[:10]  # Use a small subset for testing
    data = fetch_price_data(symbols=symbols, period=30, interval="1m")
    
        