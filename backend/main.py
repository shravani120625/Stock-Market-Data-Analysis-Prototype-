import argparse

from backend.src.analyzer import run_analysis
from backend.src.schema import init_db


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a stock market analysis and generate charts/reports."
    )
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker, for example AAPL")
    parser.add_argument("--start", default="2020-01-01", help="Start date: YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date: YYYY-MM-DD")
    parser.add_argument("--csv", default=None, help="Optional local CSV fallback path")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch fresh data from Yahoo Finance before analysis",
    )
    parser.add_argument("--db", default="backend/db/market.db", help="SQLite database path")
    return parser.parse_args()


def main():
    args = parse_args()
    init_db(args.db)

    result = run_analysis(
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        db=args.db,
        csv_path=args.csv,
        refresh=args.refresh,
    )

    print("\nStock Market Data Analyzer")
    print("-" * 32)
    print(f"Ticker: {result['ticker']}")
    print(f"Rows analyzed: {result['rows']}")
    print(f"Date range: {result['start_date']} to {result['end_date']}")
    print(f"Latest close: ${result['latest_close']:.2f}")
    print(f"Total return: {result['total_return_pct']:.2f}%")
    print(f"Annual volatility: {result['annual_volatility_pct']:.2f}%")
    print(f"Trend signal: {result['trend_signal']}")
    print("\nGenerated files:")
    for path in result["files"]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
