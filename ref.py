#!/usr/bin/env python3
# signals.py

"""
Module for generating buy/sell signals based on volatility and momentum.

Assumes price data are provided as numpy arrays of closing prices.
"""

import numpy as np
from typing import Dict, List, Tuple


def compute_volatility(prices: np.ndarray) -> float:
    """
    Computes normalized volatility: standard deviation divided by mean.

    Args:
        prices: 1D numpy array of closing prices.

    Returns:
        Normalized volatility, or 0 if input is invalid.
    """
    if prices.size == 0 or np.mean(prices) == 0:
        return 0.0
    return float(np.std(prices, ddof=0) / np.mean(prices))


def compute_momentum(prices: np.ndarray, window: int) -> float:
    """
    Computes momentum as percentage change over the given window.

    Args:
        prices: 1D numpy array of closing prices.
        window: Number of periods to look back.

    Returns:
        Momentum as (current - past) / past, or 0 if insufficient data.
    """
    if prices.size < window + 1:
        return 0.0
    past = prices[-(window + 1)]
    curr = prices[-1]
    if past == 0:
        return 0.0
    return float((curr - past) / past)


def score_universe(
    data: Dict[str, np.ndarray],
    mom_window: int = 5
) -> List[Tuple[str, float, float]]:
    """
    Scores each ticker by volatility and momentum.

    Args:
        data: Mapping of ticker to its numpy array of closing prices.
        mom_window: Number of bars for momentum calculation.

    Returns:
        List of tuples (ticker, volatility, momentum), filtered for momentum>0,
        sorted by volatility descending.
    """
    scores: List[Tuple[str, float, float]] = []
    for ticker, prices in data.items():
        vol = compute_volatility(prices)
        mom = compute_momentum(prices, mom_window)
        if mom > 0:
            scores.append((ticker, vol, mom))
    # Sort by volatility descending
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def select_long_list(
    scores: List[Tuple[str, float, float]],
    N: int
) -> List[str]:
    """
    Selects the top-N tickers to long based on scored universe.

    Args:
        scores: List of (ticker, volatility, momentum) tuples, sorted by volatility.
        N: Number of tickers to select.

    Returns:
        List of ticker symbols.
    """
    return [ticker for ticker, _, _ in scores[:N]]


def check_sell_signals(
    current_prices: Dict[str, float],
    entry_prices: Dict[str, float],
    L: float
) -> List[str]:
    """
    Identifies which tickers have met or exceeded the profit target.

    Args:
        current_prices: Mapping of ticker to latest price.
        entry_prices: Mapping of ticker to entry price.
        L: Profit threshold as decimal (e.g., 0.02 for 2%).

    Returns:
        List of tickers to sell.
    """
    to_sell: List[str] = []
    for ticker, entry in entry_prices.items():
        curr = current_prices.get(ticker, None)
        if curr is None or entry == 0:
            continue
        if (curr - entry) / entry >= L:
            to_sell.append(ticker)
    return to_sell


if __name__ == "__main__":
    # Example usage
    from data_module import fetch_price_data

    # Fetch data for default universe
    prices = fetch_price_data()
    scores = score_universe(prices, mom_window=5)
    longs = select_long_list(scores, N=3)
    print("Selected longs:", longs)

    # Simulate sell check
    current = {t: arr[-1] for t, arr in prices.items()}
    entries = {t: prices[t][0] for t in longs}
    to_sell = check_sell_signals(current, entries, L=0.02)
    print("To sell:", to_sell)
