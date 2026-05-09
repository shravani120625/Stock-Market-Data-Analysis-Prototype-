import pandas as pd
import numpy as np
import sqlite3
import json
import uuid
import datetime as dt

def run_sma_backtest(db="backend/db/market.db", ticker="AAPL", fee_bps=5, start=None, end=None):
    con = sqlite3.connect(db)
    df = pd.read_sql_query("""
      SELECT c.date, c.close, i.sma20, i.sma50
      FROM candles_daily c JOIN indicators_daily i ON i.ticker=c.ticker AND i.date=c.date
      WHERE c.ticker=? ORDER BY c.date
    """, con, params=[ticker])
    con.close()
    
    if df.empty:
        return None
        
    if start: df = df[df["date"] >= start]
    if end: df = df[df["date"] <= end]
    
    df = df.dropna().reset_index(drop=True)
    if len(df) < 2:
        return None

    # Strategy: 1 if SMA20 > SMA50 (Long), 0 otherwise (Flat)
    signal = (df["sma20"] > df["sma50"]).astype(int)
    pos = signal.shift(1).fillna(0)  # Enter next day
    
    ret = df["close"].pct_change().fillna(0.0)
    gross = pos * ret
    
    # Transaction costs
    turns = (pos.diff().abs().fillna(0) > 0).astype(int)
    cost = turns * (fee_bps / 10000.0)
    net = gross - cost

    equity = (1 + net).cumprod()
    
    # Metrics
    pnl = float(equity.iloc[-1] - 1)
    roll = net
    sharpe = float(np.sqrt(252) * (roll.mean() / (roll.std() + 1e-9)))
    peak = equity.cummax()
    dd = (equity / peak - 1).min()
    trades = int(turns.sum())
    win_rate = float((net[turns == 1] > 0).mean() if trades > 0 else 0)
    years = max(len(df) / 252.0, 1 / 252.0)
    cagr = float(equity.iloc[-1] ** (1 / years) - 1)
    gross_profit = float(net[net > 0].sum())
    gross_loss = float(abs(net[net < 0].sum()))
    profit_factor = float(gross_profit / (gross_loss + 1e-9))

    return {
      "pnl": pnl, 
      "cagr": cagr,
      "max_dd": float(dd), 
      "sharpe": sharpe, 
      "trades": trades, 
      "win_rate": win_rate,
      "profit_factor": profit_factor,
      "curve": equity.tolist(), 
      "dates": df["date"].tolist(),
      "final_value": float(equity.iloc[-1])
    }

def save_backtest(db, name, params, ticker, stats):
    if not stats:
        return None
    con = sqlite3.connect(db)
    cur = con.cursor()
    bid = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO backtests
        (id, name, params_json, start, end, ticker, pnl, max_dd, sharpe, trades, win_rate, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        bid, name, json.dumps(params), stats["dates"][0], stats["dates"][-1], ticker,
        stats["pnl"], stats["max_dd"], stats["sharpe"], stats["trades"], stats["win_rate"],
        dt.datetime.utcnow().isoformat()
    ))
    con.commit()
    con.close()
    return bid
