import datetime as dt
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
# pd.set_option("max_rows", 100)
# pd.set_option("max_columns", 20)

# import mplfinance as mpf
import pandas_ta as ta

from . import watchlist


TradeSet = Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]

def all_trades(tickers: List[str], timeframe: str, cache=True) -> Dict[str, TradeSet]:
    watch = watchlist.Watchlist(tickers, tf=timeframe, ds_name="yahoo", timed=True)
    # watch.strategy = ta.CommonStrategy # If you have a Custom Strategy, you can use it here.
    watch.load(analyze=True, verbose=False, force=True, cache=cache)

    def recent_bars(df, tf: str = "1y"):
        # All Data: 0, Last Four Years: 0.25, Last Two Years: 0.5, This Year: 1, Last Half Year: 2, Last Quarter: 4
        yearly_divisor = {
            "all": 0,
            "10y": 0.1,
            "5y": 0.2,
            "4y": 0.25,
            "3y": 1./3,
            "2y": 0.5,
            "1y": 1,
            "6mo": 2,
            "3mo": 4,
        }
        yd = yearly_divisor[tf] if tf in yearly_divisor.keys() else 0
        return int(ta.RATE["TRADING_DAYS_PER_YEAR"] / yd) if yd > 0 else df.shape[0]

    def trim(ticker):
        duration = "1y"
        asset = watch.data[ticker]
        recent = recent_bars(asset, duration)
        asset.columns = asset.columns.str.lower()
        asset.drop(columns=["dividends", "split"], errors="ignore", inplace=True)
        asset = asset.copy().tail(recent)
        return asset

    def create_trend(asset):
        # Example Long Trends
        # long = ta.sma(asset.close, 50) > ta.sma(asset.close, 200) # SMA(50) > SMA(200) "Golden/Death Cross"
        # long = ta.sma(asset.close, 10) > ta.sma(asset.close, 20) # SMA(10) > SMA(20)
        long = None
        try:
            long = ta.ema(asset.close, 10) > ta.ema(asset.close, 20)  # EMA(8) > EMA(21)
        except:
            pass
        # long = ta.increasing(ta.ema(asset.close, 50))
        # long = ta.macd(asset.close).iloc[:,1] > 0 # MACD Histogram is positive
        # long = ta.amat(asset.close, 50, 200).AMATe_LR_2  # Long Run of AMAT(50, 200) with lookback of 2 bars

        # long &= ta.increasing(ta.ema(asset.close, 50), 2)
        # Uncomment for further long restrictions, in this case when EMA(50) is increasing/sloping upwards

        # long = 1 - long # uncomment to create a short signal of the trend

        asset.ta.ema(length=10, sma=False, append=True)
        asset.ta.ema(length=20, sma=False, append=True)
        asset.ta.ema(length=50, sma=False, append=True)
        asset.ta.dema(length=50, sma=False, append=True)
        # asset.ta.xsignals(asset.ta.ema(), 10, 20, above=True)
        asset.ta.percent_return(append=True)
        print("TA Columns Added:")
        return asset, long

    def create_trade_table(asset, trendy):
        entries = trendy.TS_Entries * asset.close
        entries = entries[~np.isclose(entries, 0)]
        entries.dropna(inplace=True)
        entries.name = "Entry"

        exits = trendy.TS_Exits * asset.close
        exits = exits[~np.isclose(exits, 0)]
        exits.dropna(inplace=True)
        exits.name = "Exit"

        total_trades = trendy.TS_Trades.abs().sum()
        rt_trades = int(trendy.TS_Trades.abs().sum() // 2)

        all_trades = trendy.TS_Trades.copy().fillna(0)
        all_trades = all_trades[all_trades != 0]

        trades = pd.DataFrame({
            "Signal": all_trades,
            entries.name: entries,
            exits.name: exits
        })

        # Show some stats if there is an active trade (when there is an odd number of round trip trades)
        if total_trades % 2 != 0:
            unrealized_pnl = asset.close.iloc[-1] - entries.iloc[-1]
            unrealized_pnl_pct_change = 100 * ((asset.close.iloc[-1] / entries.iloc[-1]) - 1)
            print("Current Trade:")
            print(f"Price Entry | Last:\t{entries.iloc[-1]:.4f} | {asset.close.iloc[-1]:.4f}")
            print(f"Unrealized PnL | %:\t{unrealized_pnl:.4f} | {unrealized_pnl_pct_change:.4f}%")
        print(f"\nTrades Total | Round Trip:\t{total_trades} | {rt_trades}")
        print(f"Trade Coverage: {100 * asset.TS_Trends.sum() / asset.shape[0]:.2f}%")

        return trades

    def create_trend_signals(asset, long):
        trendy = asset.ta.tsignals(long, asbool=False, append=True)
        asset["ACTRET_1"] = trendy.TS_Trends.shift(1) * asset.PCTRET_1

        return trendy

    def create_trades(ticker) -> TradeSet:
        print(f"{ticker} {watch.data[ticker].shape}\nColumns: [', '.join(list(watch.data[ticker].columns))]")
        asset = trim(ticker)
        asset, long = create_trend(asset)
        trendy = create_trend_signals(asset, long)
        trades = create_trade_table(asset, trendy)
        print(trades.tail(2))
        return (trades, trendy, asset, long)

    return {ticker: create_trades(ticker) for ticker in tickers}
