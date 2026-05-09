from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import pandas as pd
from typing import Optional

# Import local modules
from backend.src.ingest import upsert_daily
from backend.src.indicators import compute_indicators, detect_patterns, generate_signals
from backend.src.backtest import run_sma_backtest, save_backtest
from backend.src.alerts import create_alert, evaluate_alerts, list_alerts
from backend.src.portfolio import add_transaction, portfolio_summary
from backend.src.schema import init_db
from backend.src.market import (
    add_watchlist_item,
    generate_signal_record,
    get_news_items,
    latest_snapshot,
    list_watchlist,
    market_overview,
    risk_metrics,
    upsert_live_snapshot,
)

GLOSSARY = [
    {"short_form": "API", "full_form": "Application Programming Interface"},
    {"short_form": "OHLCV", "full_form": "Open, High, Low, Close, Volume"},
    {"short_form": "CSV", "full_form": "Comma-Separated Values"},
    {"short_form": "SQL", "full_form": "Structured Query Language"},
    {"short_form": "SMA", "full_form": "Simple Moving Average"},
    {"short_form": "EMA", "full_form": "Exponential Moving Average"},
    {"short_form": "RSI", "full_form": "Relative Strength Index"},
    {"short_form": "MACD", "full_form": "Moving Average Convergence Divergence"},
    {"short_form": "BB", "full_form": "Bollinger Bands"},
    {"short_form": "ATR", "full_form": "Average True Range"},
    {"short_form": "OBV", "full_form": "On-Balance Volume"},
    {"short_form": "VWAP", "full_form": "Volume Weighted Average Price"},
    {"short_form": "PnL", "full_form": "Profit and Loss"},
    {"short_form": "CAGR", "full_form": "Compound Annual Growth Rate"},
    {"short_form": "VaR", "full_form": "Value at Risk"},
    {"short_form": "Max DD", "full_form": "Maximum Drawdown"},
    {"short_form": "OI", "full_form": "Open Interest"},
    {"short_form": "IV", "full_form": "Implied Volatility"},
]

app = FastAPI(
    title="Stock Market Data Analyzer API",
    description=(
        "Professional educational market analytics API for OHLCV data, technical indicators, "
        "signals, portfolio analytics, risk metrics, backtesting, alerts, and news sentiment."
    ),
    version="1.0.0",
)
DB = "backend/db/market.db"
init_db(DB)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BacktestReq(BaseModel):
    ticker: str
    fee_bps: int = 5
    start: Optional[str] = None
    end: Optional[str] = None

class TransactionReq(BaseModel):
    ticker: str
    side: str
    qty: float
    price: float
    fees: float = 0.0
    ts: Optional[str] = None

class AlertReq(BaseModel):
    ticker: str
    rule: str
    threshold: float

class WatchlistReq(BaseModel):
    ticker: str
    name: str = "Default"
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Stock Market Data Analyzer API",
        "description": "Educational market analytics backend. Not financial advice.",
    }

@app.get("/glossary")
def get_glossary():
    return GLOSSARY

@app.post("/refresh/{ticker}")
def refresh_data(ticker: str):
    try:
        upsert_daily(DB, ticker)
        compute_indicators(DB, ticker)
        upsert_live_snapshot(DB, ticker)
        generate_signal_record(DB, ticker)
        return {"status": "success", "message": f"Data refreshed for {ticker}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chart/{ticker}")
def get_chart_data(ticker: str, days: int = 252):
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT c.date, c.open, c.high, c.low, c.close, c.volume,
                   i.sma20, i.sma50, i.rsi14, i.macd, i.macd_signal,
                   i.bb_upper, i.bb_mid, i.bb_lower
            FROM candles_daily c 
            LEFT JOIN indicators_daily i ON i.ticker=c.ticker AND i.date=c.date
            WHERE c.ticker=? 
            ORDER BY c.date DESC 
            LIMIT ?
        """, [ticker.upper(), days]).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()

@app.post("/backtest/sma")
def backtest_sma(req: BacktestReq):
    stats = run_sma_backtest(DB, req.ticker.upper(), req.fee_bps, req.start, req.end)
    if not stats:
        raise HTTPException(status_code=404, detail="Not enough data for backtest")
    
    bid = save_backtest(DB, "SMA20>50 Cross", req.dict(), req.ticker.upper(), stats)
    return {"id": bid, "stats": stats}

@app.get("/symbols")
def list_symbols():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT DISTINCT ticker FROM candles_daily").fetchall()
        return [r["ticker"] for r in rows]
    finally:
        conn.close()

@app.get("/market/overview")
def get_market_overview():
    return market_overview(DB)

@app.get("/live/{ticker}")
def get_live_price(ticker: str):
    snapshot = upsert_live_snapshot(DB, ticker.upper())
    if not snapshot:
        raise HTTPException(status_code=404, detail="No live snapshot available")
    return snapshot

@app.get("/signals/{ticker}")
def get_signal(ticker: str):
    signal = generate_signal_record(DB, ticker.upper())
    if not signal:
        raise HTTPException(status_code=404, detail="No signal data available")
    return signal

@app.post("/watchlist")
def add_to_watchlist(req: WatchlistReq):
    item_id = add_watchlist_item(
        DB,
        req.ticker,
        name=req.name,
        target_price=req.target_price,
        stop_loss=req.stop_loss,
    )
    return {"id": item_id, "status": "saved"}

@app.get("/watchlist")
def get_watchlist(name: str = "Default"):
    return list_watchlist(DB, name=name)

@app.post("/portfolio/tx")
def add_portfolio_transaction(req: TransactionReq):
    try:
        tx_id = add_transaction(
            DB,
            req.ticker,
            req.side,
            req.qty,
            req.price,
            fees=req.fees,
            ts=req.ts,
        )
        return {"id": tx_id, "status": "saved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolio")
def get_portfolio():
    return portfolio_summary(DB)

@app.post("/alerts")
def add_alert(req: AlertReq):
    try:
        alert_id = create_alert(DB, req.ticker, req.rule, req.threshold)
        return {"id": alert_id, "status": "active"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/alerts")
def get_alerts():
    return list_alerts(DB)

@app.post("/alerts/evaluate")
def run_alert_evaluation():
    return {"fired": evaluate_alerts(DB)}

@app.get("/latest/{ticker}")
def get_latest(ticker: str):
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT c.*, i.sma20, i.sma50, i.rsi14, i.bb_upper, i.bb_lower
            FROM candles_daily c 
            LEFT JOIN indicators_daily i ON i.ticker=c.ticker AND i.date=c.date
            WHERE c.ticker=? 
            ORDER BY c.date DESC 
            LIMIT 1
        """, [ticker.upper()]).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No data found")
        return dict(row)
    finally:
        conn.close()

@app.get("/analytics/{ticker}")
def get_analytics(ticker: str):
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT c.*, i.sma20, i.sma50, i.rsi14 
            FROM candles_daily c 
            LEFT JOIN indicators_daily i ON i.ticker=c.ticker AND i.date=c.date
            WHERE c.ticker=? ORDER BY c.date DESC LIMIT 100
        """, conn, params=[ticker.upper()])
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data")
            
        df = df.sort_values('date')
        patterns = detect_patterns(df)
        signal, reason = generate_signals(df)
        
        risk = risk_metrics(DB, ticker.upper())
        signal_record = generate_signal_record(DB, ticker.upper())
        
        return {
            "ticker": ticker,
            "patterns": patterns,
            "signal": signal_record["signal"] if signal_record else signal,
            "signal_reason": signal_record["reason"] if signal_record else reason,
            "signal_strength": signal_record["strength"] if signal_record else 0.4,
            "risk": risk,
        }
    finally:
        conn.close()

@app.get("/news/{ticker}")
def get_news(ticker: str):
    return get_news_items(DB, ticker.upper())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
