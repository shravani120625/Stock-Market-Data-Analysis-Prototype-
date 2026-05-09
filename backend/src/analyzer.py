import os
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from backend.src.indicators import compute_indicators
from backend.src.ingest import fetch_daily, upsert_daily


REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]


def ensure_output_dirs():
    for folder in ["data", "outputs", "images", "reports"]:
        Path(folder).mkdir(parents=True, exist_ok=True)


def normalize_price_frame(df):
    """Return a beginner-friendly, predictable OHLCV dataframe."""
    df = df.copy()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    if "adj_close" not in df.columns and "adj_close*" in df.columns:
        df.rename(columns={"adj_close*": "adj_close"}, inplace=True)
    if "adj_close" not in df.columns and "adjusted_close" in df.columns:
        df.rename(columns={"adjusted_close": "adj_close"}, inplace=True)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[REQUIRED_COLUMNS]
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.date.astype(str)
    return df


def load_from_csv(csv_path):
    return normalize_price_frame(pd.read_csv(csv_path))


def load_from_db(db, ticker, start=None, end=None):
    con = sqlite3.connect(db)
    query = """
        SELECT date, open, high, low, close, adj_close, volume
        FROM candles_daily
        WHERE ticker=?
    """
    params = [ticker.upper()]
    if start:
        query += " AND date >= ?"
        params.append(start)
    if end:
        query += " AND date <= ?"
        params.append(end)
    query += " ORDER BY date"
    df = pd.read_sql_query(query, con, params=params)
    con.close()
    return normalize_price_frame(df) if not df.empty else df


def load_market_data(ticker, start, end, db, csv_path=None, refresh=False):
    ticker = ticker.upper()
    if csv_path:
        return load_from_csv(csv_path)

    if refresh:
        upsert_daily(db, ticker)
        compute_indicators(db, ticker)

    df = load_from_db(db, ticker, start, end)
    if not df.empty:
        return df

    fetched = fetch_daily(ticker, start=start, end=end)
    if fetched.empty:
        raise ValueError(
            f"No data found for {ticker}. Try --refresh, another ticker, or --csv data/sample.csv."
        )
    return normalize_price_frame(fetched)


def add_analysis_columns(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["daily_return"] = df["close"].pct_change()
    df["sma20"] = df["close"].rolling(window=20).mean()
    df["sma50"] = df["close"].rolling(window=50).mean()
    df["volatility20"] = df["daily_return"].rolling(window=20).std() * (252**0.5)
    df["cumulative_return"] = (1 + df["daily_return"].fillna(0)).cumprod() - 1
    return df


def build_summary(ticker, df):
    returns = df["daily_return"].dropna()
    first_close = float(df["close"].iloc[0])
    latest_close = float(df["close"].iloc[-1])
    total_return = (latest_close / first_close - 1) * 100
    annual_volatility = float(returns.std() * (252**0.5) * 100) if not returns.empty else 0.0
    avg_daily_return = float(returns.mean() * 100) if not returns.empty else 0.0
    high_row = df.loc[df["high"].idxmax()]
    low_row = df.loc[df["low"].idxmin()]

    signal, reason = "HOLD", "Wait for trend confirmation"
    signal_rows = df.dropna(subset=["sma20", "sma50"]).tail(2)
    if len(signal_rows) == 2:
        prev = signal_rows.iloc[0]
        last = signal_rows.iloc[1]
        if prev["sma20"] < prev["sma50"] and last["sma20"] >= last["sma50"]:
            signal, reason = "BUY", "Golden Cross (SMA 20 crossed above SMA 50)"
        elif prev["sma20"] > prev["sma50"] and last["sma20"] <= last["sma50"]:
            signal, reason = "SELL", "Death Cross (SMA 20 crossed below SMA 50)"
        elif last["sma20"] > last["sma50"]:
            signal, reason = "HOLD", "Short-term trend is above long-term trend"
        else:
            signal, reason = "HOLD", "Short-term trend is below long-term trend"
    if pd.isna(df["sma50"].iloc[-1]):
        signal, reason = "HOLD", "Not enough rows for SMA50 trend"

    return {
        "ticker": ticker.upper(),
        "rows": int(len(df)),
        "start_date": df["date"].iloc[0].date().isoformat(),
        "end_date": df["date"].iloc[-1].date().isoformat(),
        "latest_close": latest_close,
        "first_close": first_close,
        "total_return_pct": float(total_return),
        "avg_daily_return_pct": avg_daily_return,
        "annual_volatility_pct": annual_volatility,
        "highest_price": float(high_row["high"]),
        "highest_price_date": high_row["date"].date().isoformat(),
        "lowest_price": float(low_row["low"]),
        "lowest_price_date": low_row["date"].date().isoformat(),
        "trend_signal": f"{signal} - {reason}",
    }


def save_charts(ticker, df):
    sns.set_theme(style="whitegrid")
    ticker = ticker.upper()
    files = []

    price_path = Path("images") / f"{ticker}_closing_price.png"
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["close"], label="Close", color="#2563eb")
    plt.title(f"{ticker} Closing Price")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.tight_layout()
    plt.savefig(price_path, dpi=150)
    plt.close()
    files.append(str(price_path))

    ma_path = Path("images") / f"{ticker}_moving_averages.png"
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["close"], label="Close", color="#111827", linewidth=1.2)
    plt.plot(df["date"], df["sma20"], label="SMA 20", color="#16a34a")
    plt.plot(df["date"], df["sma50"], label="SMA 50", color="#dc2626")
    plt.title(f"{ticker} Moving Average Trend")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ma_path, dpi=150)
    plt.close()
    files.append(str(ma_path))

    return_path = Path("images") / f"{ticker}_daily_returns.png"
    plt.figure(figsize=(12, 6))
    sns.histplot(df["daily_return"].dropna() * 100, bins=50, kde=True, color="#7c3aed")
    plt.title(f"{ticker} Daily Return Distribution")
    plt.xlabel("Daily Return (%)")
    plt.ylabel("Trading Days")
    plt.tight_layout()
    plt.savefig(return_path, dpi=150)
    plt.close()
    files.append(str(return_path))

    vol_path = Path("images") / f"{ticker}_volatility.png"
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["volatility20"] * 100, label="20-Day Annualized Volatility", color="#f97316")
    plt.title(f"{ticker} Rolling Volatility")
    plt.xlabel("Date")
    plt.ylabel("Volatility (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(vol_path, dpi=150)
    plt.close()
    files.append(str(vol_path))

    return files


def write_report(summary, chart_files):
    path = Path("reports") / f"{summary['ticker']}_analysis_report.md"
    lines = [
        f"# {summary['ticker']} Stock Analysis Report",
        "",
        "## Summary",
        f"- Date range: {summary['start_date']} to {summary['end_date']}",
        f"- Rows analyzed: {summary['rows']}",
        f"- First close: ${summary['first_close']:.2f}",
        f"- Latest close: ${summary['latest_close']:.2f}",
        f"- Total return: {summary['total_return_pct']:.2f}%",
        f"- Average daily return: {summary['avg_daily_return_pct']:.4f}%",
        f"- Annual volatility: {summary['annual_volatility_pct']:.2f}%",
        f"- Highest price: ${summary['highest_price']:.2f} on {summary['highest_price_date']}",
        f"- Lowest price: ${summary['lowest_price']:.2f} on {summary['lowest_price_date']}",
        f"- Current signal: {summary['trend_signal']}",
        "",
        "## Generated Charts",
    ]
    lines.extend(f"- {file}" for file in chart_files)
    lines.extend(
        [
            "",
            "## Interpretation",
            "Moving averages help smooth noisy price movement and identify trend direction.",
            "Daily returns show short-term performance, while volatility gives a risk estimate.",
            "",
            "## Disclaimer",
            "This project is for educational purposes only and is not financial advice.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def run_analysis(ticker="AAPL", start="2020-01-01", end=None, db="backend/db/market.db", csv_path=None, refresh=False):
    ensure_output_dirs()
    ticker = ticker.upper()
    df = load_market_data(ticker, start, end, db, csv_path=csv_path, refresh=refresh)
    df = add_analysis_columns(df)

    output_csv = Path("outputs") / f"{ticker}_analysis_dataset.csv"
    df.to_csv(output_csv, index=False)

    summary = build_summary(ticker, df)
    chart_files = save_charts(ticker, df)
    report_file = write_report(summary, chart_files)

    summary_file = Path("outputs") / f"{ticker}_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_file, index=False)

    summary["files"] = [str(output_csv), str(summary_file), *chart_files, report_file]
    return summary
