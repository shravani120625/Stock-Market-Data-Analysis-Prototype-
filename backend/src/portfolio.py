import sqlite3
import uuid
from datetime import datetime

import pandas as pd


def add_transaction(db, ticker, side, qty, price, fees=0.0, ts=None):
    side = side.upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    if qty <= 0 or price <= 0:
        raise ValueError("qty and price must be positive")

    con = sqlite3.connect(db)
    cur = con.cursor()
    tx_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO portfolio_tx(id, ticker, ts, side, qty, price, fees)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx_id,
            ticker.upper(),
            ts or datetime.utcnow().isoformat(),
            side,
            float(qty),
            float(price),
            float(fees),
        ),
    )
    con.commit()
    con.close()
    return tx_id


def positions(db="backend/db/market.db"):
    con = sqlite3.connect(db)
    tx = pd.read_sql_query("SELECT * FROM portfolio_tx ORDER BY ts", con)
    con.close()

    if tx.empty:
        return pd.DataFrame(columns=["ticker", "qty", "avg_cost", "invested"])

    tx["signed_qty"] = tx["qty"].where(tx["side"] == "BUY", -tx["qty"])
    tx["cash_flow"] = tx["qty"] * tx["price"] + tx["fees"]

    rows = []
    for ticker, group in tx.groupby("ticker"):
        buy_rows = group[group["side"] == "BUY"]
        qty = float(group["signed_qty"].sum())
        invested = float(buy_rows["cash_flow"].sum())
        buy_qty = float(buy_rows["qty"].sum())
        avg_cost = invested / buy_qty if buy_qty else 0.0
        rows.append(
            {
                "ticker": ticker,
                "qty": qty,
                "avg_cost": avg_cost,
                "invested": invested,
            }
        )

    return pd.DataFrame(rows)


def portfolio_summary(db="backend/db/market.db"):
    pos = positions(db)
    if pos.empty:
        return []

    con = sqlite3.connect(db)
    latest = pd.read_sql_query(
        """
        SELECT c.ticker, c.close, c.date
        FROM candles_daily c
        JOIN (
            SELECT ticker, MAX(date) AS max_date
            FROM candles_daily
            GROUP BY ticker
        ) x ON x.ticker = c.ticker AND x.max_date = c.date
        """,
        con,
    )
    con.close()

    merged = pos.merge(latest, on="ticker", how="left")
    merged["market_value"] = merged["qty"] * merged["close"].fillna(0)
    merged["unrealized_pnl"] = merged["market_value"] - (merged["qty"] * merged["avg_cost"])
    return merged.to_dict(orient="records")
