import sqlite3
import uuid
from datetime import datetime

import numpy as np
import pandas as pd

from backend.src.indicators import detect_patterns, generate_signals


def _rows(con, sql, params=()):
    con.row_factory = sqlite3.Row
    return [dict(row) for row in con.execute(sql, params).fetchall()]


def latest_snapshot(db="backend/db/market.db", ticker="AAPL"):
    con = sqlite3.connect(db)
    df = pd.read_sql_query(
        """
        SELECT date, open, high, low, close, volume
        FROM candles_daily
        WHERE ticker=?
        ORDER BY date DESC
        LIMIT 2
        """,
        con,
        params=[ticker.upper()],
    )
    con.close()
    if df.empty:
        return None

    today = df.iloc[0]
    previous_close = float(df.iloc[1]["close"]) if len(df) > 1 else float(today["open"])
    price = float(today["close"])
    spread = max(price * 0.0005, 0.01)
    change = price - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0
    vwap = float((today["high"] + today["low"] + today["close"]) / 3)

    return {
        "ticker": ticker.upper(),
        "ts": today["date"],
        "price": price,
        "bid": price - spread,
        "ask": price + spread,
        "day_change": change,
        "day_change_pct": change_pct,
        "day_high": float(today["high"]),
        "day_low": float(today["low"]),
        "vwap": vwap,
        "volume": int(today["volume"]),
        "source": "historical_close_simulated_live",
    }


def upsert_live_snapshot(db="backend/db/market.db", ticker="AAPL"):
    snapshot = latest_snapshot(db, ticker)
    if not snapshot:
        return None
    con = sqlite3.connect(db)
    con.execute(
        """
        INSERT OR REPLACE INTO live_prices
        (ticker, ts, price, bid, ask, day_change, day_change_pct, day_high, day_low, vwap, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot["ticker"],
            snapshot["ts"],
            snapshot["price"],
            snapshot["bid"],
            snapshot["ask"],
            snapshot["day_change"],
            snapshot["day_change_pct"],
            snapshot["day_high"],
            snapshot["day_low"],
            snapshot["vwap"],
            snapshot["volume"],
            snapshot["source"],
        ),
    )
    con.commit()
    con.close()
    return snapshot


def risk_metrics(db="backend/db/market.db", ticker="AAPL", benchmark="AAPL"):
    con = sqlite3.connect(db)
    prices = pd.read_sql_query(
        "SELECT date, close FROM candles_daily WHERE ticker=? ORDER BY date",
        con,
        params=[ticker.upper()],
    )
    bench = pd.read_sql_query(
        "SELECT date, close FROM candles_daily WHERE ticker=? ORDER BY date",
        con,
        params=[benchmark.upper()],
    )
    con.close()

    if len(prices) < 2:
        return {
            "volatility": 0.0,
            "var_95": 0.0,
            "max_drawdown": 0.0,
            "beta": None,
            "alpha": None,
            "sharpe": 0.0,
        }

    prices["return"] = prices["close"].pct_change()
    returns = prices["return"].dropna()
    equity = (1 + returns).cumprod()
    drawdown = equity / equity.cummax() - 1

    beta = None
    alpha = None
    if benchmark.upper() != ticker.upper() and len(bench) > 2:
        bench["benchmark_return"] = bench["close"].pct_change()
        merged = prices[["date", "return"]].merge(
            bench[["date", "benchmark_return"]], on="date", how="inner"
        ).dropna()
        if len(merged) > 2 and merged["benchmark_return"].var() != 0:
            beta = float(merged["return"].cov(merged["benchmark_return"]) / merged["benchmark_return"].var())
            alpha = float((merged["return"].mean() - beta * merged["benchmark_return"].mean()) * 252)

    return {
        "volatility": float(returns.std() * np.sqrt(252)),
        "var_95": float(np.percentile(returns, 5)),
        "max_drawdown": float(drawdown.min()),
        "beta": beta,
        "alpha": alpha,
        "sharpe": float(np.sqrt(252) * returns.mean() / (returns.std() + 1e-9)),
    }


def generate_signal_record(db="backend/db/market.db", ticker="AAPL"):
    ticker = ticker.upper()
    con = sqlite3.connect(db)
    df = pd.read_sql_query(
        """
        SELECT c.date, c.open, c.high, c.low, c.close, i.sma20, i.sma50, i.rsi14, i.macd, i.macd_signal
        FROM candles_daily c
        LEFT JOIN indicators_daily i ON i.ticker=c.ticker AND i.date=c.date
        WHERE c.ticker=?
        ORDER BY c.date DESC
        LIMIT 100
        """,
        con,
        params=[ticker],
    )
    if df.empty:
        con.close()
        return None

    df = df.sort_values("date")
    signal, reason = generate_signals(df)
    if signal == "HOLD":
        last = df.iloc[-1]
        if pd.notna(last.get("macd")) and pd.notna(last.get("macd_signal")):
            if last["macd"] > last["macd_signal"]:
                signal, reason = "BUY", "MACD bullish momentum"
            elif last["macd"] < last["macd_signal"]:
                signal, reason = "SELL", "MACD bearish momentum"

    strength = {"BUY": 0.75, "SELL": 0.75, "HOLD": 0.4}.get(signal, 0.4)
    record = {
        "ticker": ticker,
        "date": str(df.iloc[-1]["date"]),
        "signal": signal,
        "reason": reason,
        "strength": strength,
        "created_at": datetime.utcnow().isoformat(),
        "patterns": detect_patterns(df),
    }

    con.execute(
        """
        INSERT OR REPLACE INTO signals(ticker, date, signal, reason, strength, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            record["ticker"],
            record["date"],
            record["signal"],
            record["reason"],
            record["strength"],
            record["created_at"],
        ),
    )
    con.commit()
    con.close()
    return record


def market_overview(db="backend/db/market.db"):
    con = sqlite3.connect(db)
    symbols = [row["ticker"] for row in _rows(con, "SELECT DISTINCT ticker FROM candles_daily ORDER BY ticker")]
    snapshots = []
    for ticker in symbols:
        snap = latest_snapshot(db, ticker)
        if snap:
            snapshots.append(snap)
    con.close()

    gainers = sorted(snapshots, key=lambda row: row["day_change_pct"], reverse=True)[:5]
    losers = sorted(snapshots, key=lambda row: row["day_change_pct"])[:5]
    advancing = sum(1 for row in snapshots if row["day_change_pct"] > 0)
    declining = sum(1 for row in snapshots if row["day_change_pct"] < 0)
    breadth = advancing / max(declining, 1)

    return {
        "count": len(snapshots),
        "top_gainers": gainers,
        "top_losers": losers,
        "advance_decline": {
            "advancing": advancing,
            "declining": declining,
            "ratio": breadth,
        },
    }


def add_watchlist_item(db, ticker, name="Default", target_price=None, stop_loss=None):
    con = sqlite3.connect(db)
    item_id = str(uuid.uuid4())
    con.execute(
        """
        INSERT OR REPLACE INTO watchlists(id, name, ticker, target_price, stop_loss, created_at)
        VALUES (
            COALESCE((SELECT id FROM watchlists WHERE name=? AND ticker=?), ?),
            ?, ?, ?, ?, ?
        )
        """,
        (
            name,
            ticker.upper(),
            item_id,
            name,
            ticker.upper(),
            target_price,
            stop_loss,
            datetime.utcnow().isoformat(),
        ),
    )
    con.commit()
    con.close()
    return item_id


def list_watchlist(db="backend/db/market.db", name="Default"):
    con = sqlite3.connect(db)
    items = _rows(
        con,
        "SELECT id, name, ticker, target_price, stop_loss, created_at FROM watchlists WHERE name=? ORDER BY ticker",
        [name],
    )
    con.close()
    for item in items:
        item["live"] = latest_snapshot(db, item["ticker"])
    return items


def seed_news(db="backend/db/market.db", ticker="AAPL"):
    ticker = ticker.upper()
    sample = [
        (f"{ticker} price trend watched by market analysts", "MarketWire", "Neutral", 0.05),
        (f"{ticker} technical momentum improves after recent close", "FinanceDaily", "Bullish", 0.35),
        (f"Risk managers monitor volatility in {ticker}", "RiskDesk", "Neutral", 0.0),
    ]
    con = sqlite3.connect(db)
    for title, source, sentiment, score in sample:
        con.execute(
            """
            INSERT OR IGNORE INTO news(id, ticker, published_at, title, source, sentiment, score, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                ticker,
                datetime.utcnow().isoformat(),
                title,
                source,
                sentiment,
                score,
                "",
            ),
        )
    con.commit()
    con.close()


def get_news_items(db="backend/db/market.db", ticker="AAPL"):
    seed_news(db, ticker)
    con = sqlite3.connect(db)
    rows = _rows(
        con,
        """
        SELECT title, sentiment, source, score, published_at, url
        FROM news
        WHERE ticker=?
        ORDER BY published_at DESC
        LIMIT 10
        """,
        [ticker.upper()],
    )
    con.close()
    return rows
