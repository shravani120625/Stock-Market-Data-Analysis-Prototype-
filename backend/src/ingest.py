import yfinance as yf
import pandas as pd
import sqlite3
import datetime as dt
import os

def fetch_daily(ticker: str, start="2015-01-01", end=None):
    print(f"Fetching data for {ticker}...")
    try:
        df = yf.download(ticker, start=start, end=end or dt.date.today().isoformat(), auto_adjust=False)
        if df.empty:
            print(f"No data found for {ticker}")
            return pd.DataFrame()
            
        df = df.rename(columns=str.lower).reset_index()
        df["Date"] = pd.to_datetime(df["Date"]).dt.date.astype(str)
        df.rename(columns={"adj close": "adj_close", "Date": "date"}, inplace=True)
        return df[["date", "open", "high", "low", "close", "adj_close", "volume"]]
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

def upsert_daily(db="backend/db/market.db", ticker="AAPL"):
    df = fetch_daily(ticker)
    if df.empty:
        return
        
    con = sqlite3.connect(db)
    cur = con.cursor()
    
    # Use list of tuples for executemany
    data = [(ticker, *r) for r in df.itertuples(index=False, name=None)]
    
    cur.executemany("""
        INSERT OR REPLACE INTO candles_daily
        (ticker, date, open, high, low, close, adj_close, volume)
        VALUES (?,?,?,?,?,?,?,?)
    """, data)
    
    con.commit()
    con.close()
    print(f"Successfully updated {len(df)} records for {ticker}")

if __name__ == "__main__":
    upsert_daily()
