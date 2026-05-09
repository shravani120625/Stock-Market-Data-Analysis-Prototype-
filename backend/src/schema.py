import sqlite3
import os

def init_db(db_path="backend/db/market.db"):
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    # Create Tables
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS symbols(
      ticker TEXT PRIMARY KEY, name TEXT, exchange TEXT, currency TEXT
    );

    CREATE TABLE IF NOT EXISTS stocks(
      ticker TEXT PRIMARY KEY,
      name TEXT,
      exchange TEXT,
      sector TEXT,
      industry TEXT,
      currency TEXT,
      active INT DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS candles_daily(
      ticker TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, adj_close REAL, volume INTEGER,
      PRIMARY KEY (ticker, date)
    );

    CREATE TABLE IF NOT EXISTS indicators_daily(
      ticker TEXT, date TEXT,
      sma20 REAL, sma50 REAL, rsi14 REAL, macd REAL, macd_signal REAL, macd_hist REAL,
      bb_upper REAL, bb_mid REAL, bb_lower REAL,
      PRIMARY KEY (ticker, date)
    );

    CREATE TABLE IF NOT EXISTS live_prices(
      ticker TEXT PRIMARY KEY,
      ts TEXT,
      price REAL,
      bid REAL,
      ask REAL,
      day_change REAL,
      day_change_pct REAL,
      day_high REAL,
      day_low REAL,
      vwap REAL,
      volume INTEGER,
      source TEXT
    );

    CREATE TABLE IF NOT EXISTS signals(
      ticker TEXT,
      date TEXT,
      signal TEXT,
      reason TEXT,
      strength REAL,
      created_at TEXT,
      PRIMARY KEY (ticker, date, reason)
    );

    CREATE TABLE IF NOT EXISTS news(
      id TEXT PRIMARY KEY,
      ticker TEXT,
      published_at TEXT,
      title TEXT,
      source TEXT,
      sentiment TEXT,
      score REAL,
      url TEXT
    );

    CREATE TABLE IF NOT EXISTS backtests(
      id TEXT PRIMARY KEY, name TEXT, params_json TEXT, start TEXT, end TEXT,
      ticker TEXT, pnl REAL, max_dd REAL, sharpe REAL, trades INT, win_rate REAL, created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS portfolio_tx(
      id TEXT PRIMARY KEY, ticker TEXT, ts TEXT, side TEXT, qty REAL, price REAL, fees REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS watchlists(
      id TEXT PRIMARY KEY,
      name TEXT,
      ticker TEXT,
      target_price REAL,
      stop_loss REAL,
      created_at TEXT,
      UNIQUE(name, ticker)
    );

    CREATE TABLE IF NOT EXISTS alerts(
      id TEXT PRIMARY KEY, ticker TEXT, rule TEXT, threshold REAL, active INT DEFAULT 1, last_fired TEXT
    );
    """)
    
    con.commit()
    con.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
