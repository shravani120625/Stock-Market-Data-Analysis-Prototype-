import time
import datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import yfinance as yf
from backend.src.ingest import fetch_daily, upsert_daily
from backend.src.indicators import compute_indicators
from backend.src.alerts import evaluate_alerts

DB = "backend/db/market.db"
WATCHLIST = ["AAPL", "TSLA", "BTC-USD", "NVDA", "MSFT"]

def live_update_job():
    print(f"[{dt.datetime.now()}] Running Real-time Update...")
    for ticker in WATCHLIST:
        try:
            # Update historical + latest candle
            upsert_daily(DB, ticker)
            compute_indicators(DB, ticker)
            print(f"  - {ticker} synced.")
        except Exception as e:
            print(f"  - Error updating {ticker}: {e}")
    fired = evaluate_alerts(DB)
    for alert in fired:
        print(f"ALERT: {alert['ticker']} {alert['rule']} fired on {alert['date']}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every 5 minutes (yfinance free tier limitation, don't spam too hard)
    scheduler.add_job(live_update_job, 'interval', minutes=5)
    scheduler.start()
    print("🚀 Real-time Scheduler Started (Polling every 5 mins)")
    
    try:
        # Initial run
        live_update_job()
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler()
