import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import tqdm


def fetch_price_data(tickers: Optional[List[str]] = None,
                     period: int = 30,
                     interval: str = "1m") -> Dict[str, pd.DataFrame]:
    """
    Fetches historical intraday price data for a list of tickers.

    Args:
        tickers: List of stock tickers as strings. If None, uses UNIVERSE.
        period: Data period to download (e.g., '30m', '1d', '5d').
        interval: Data interval (e.g., '1m', '2m', '5m').

    Returns:
        Dictionary mapping each ticker to its corresponding DataFrame of price data.
        DataFrame columns: ['Open', 'High', 'Low', 'Close', 'Volume'].
        Only tickers with non-empty data are included.
    """
    symbols = tickers
    data: Dict[str, pd.DataFrame] = {}

    for symbol in tqdm.tqdm(symbols):
        df = yf.Ticker(symbol).history(period="1d", interval=interval, auto_adjust=False)
        
        # Get the last 'period' minutes of data as numpy array
        prices = np.array(df["Close"][-period:].values)
        data[symbol] = prices

    return data
'''

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
'''


if __name__ == "__main__":
    from parameters import Parameters
    symbols = Parameters.symbols[:10]  # Use a small subset for testing
    data = fetch_price_data(symbols=symbols, period=30, interval="1m")
    
        