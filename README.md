# Stock Market Data Analyzer

An industry-oriented Python project for collecting public market data, computing financial indicators, running strategy backtests, serving analytics through FastAPI, and visualizing results in a professional Streamlit or Next.js dashboard.

**Author:** Shravani  
**GitHub:** [https://github.com/shravani120625/Stock-Market-Data-Analysis-Prototype-](https://github.com/shravani120625/Stock-Market-Data-Analysis-Prototype-)  
**LinkedIn:** [https://www.linkedin.com/in/shravani-hande-a443ab331](https://www.linkedin.com/in/shravani-hande-a443ab331)

> Disclaimer: This project is for education and portfolio building only. It is not financial advice.

## Problem Statement

Investors, analysts, traders, and finance teams need clean market data, repeatable calculations, and clear visual dashboards to understand price movement, trend, risk, and portfolio performance. This project automates a workflow that is often done manually in spreadsheets:

```text
Stock data collection -> data cleaning -> trend analysis -> moving averages
-> returns calculation -> risk analysis -> visualization -> report generation
```

## Industry Relevance

FinTech companies, brokers, research teams, and quantitative teams use similar pipelines for market tracking, watchlists, investment research, alerts, backtesting, and portfolio dashboards. This project demonstrates practical skills for Python Developer, Data Analyst, Financial Analyst, Business Analyst, and FinTech roles.

## Features

- Daily OHLCV (Open, High, Low, Close, Volume) data ingestion from Yahoo Finance
- CSV (Comma-Separated Values) fallback for offline analysis
- SQLite database storage for prices, indicators, live snapshots, signals, watchlists, alerts, portfolio transactions, and news
- Technical indicators: SMA, RSI, MACD, Bollinger Bands, VWAP-style snapshot, and volatility
- Signal generation using moving-average, RSI, and MACD logic
- Candlestick pattern detection such as Doji, Hammer, and Bullish Engulfing
- Portfolio analytics with holdings, average cost, market value, and PnL
- Risk metrics such as volatility, Sharpe ratio, VaR, and maximum drawdown
- Advisor Review mode with investor-profile and suitability-style educational checks
- Backtesting metrics such as CAGR, Sharpe ratio, maximum drawdown, win rate, and profit factor
- News and sentiment simulation for educational dashboard workflows
- FastAPI backend and professional Streamlit dashboard

## Full Forms Used In This Project

| Short Form | Full Form | Meaning |
| --- | --- | --- |
| API | Application Programming Interface | Connects frontend dashboard with backend analytics |
| OHLCV | Open, High, Low, Close, Volume | Core stock market candle data |
| CSV | Comma-Separated Values | Simple file format for local datasets |
| SQL | Structured Query Language | Query language used with SQLite |
| SMA | Simple Moving Average | Average price over a fixed period |
| EMA | Exponential Moving Average | Moving average weighted toward recent prices |
| RSI | Relative Strength Index | Momentum indicator for overbought/oversold zones |
| MACD | Moving Average Convergence Divergence | Trend and momentum indicator |
| BB | Bollinger Bands | Volatility bands around a moving average |
| ATR | Average True Range | Volatility indicator based on trading range |
| OBV | On-Balance Volume | Volume-based trend indicator |
| VWAP | Volume Weighted Average Price | Average price weighted by volume |
| PnL | Profit and Loss | Gain or loss on portfolio/strategy |
| CAGR | Compound Annual Growth Rate | Annualized return estimate |
| VaR | Value at Risk | Estimated downside loss at a confidence level |
| Max DD | Maximum Drawdown | Largest peak-to-trough decline |
| OI | Open Interest | Active derivatives contracts |
| IV | Implied Volatility | Market-implied expected volatility |

## Tech Stack

- Backend: Python, FastAPI, Uvicorn
- Data Analysis: Pandas, NumPy, yfinance, ta
- Visualization: Plotly, Matplotlib, Seaborn, Streamlit
- Database: SQLite
- Optional Frontend: Next.js and Recharts

## Folder Structure

```text
Stock-Market-Data-Analyzer/
|-- backend/              # FastAPI API, core Python modules, database, CLI runner
|   |-- api/              # FastAPI endpoints
|   |-- db/               # SQLite database
|   |-- src/              # Ingestion, indicators, signals, risk, alerts, portfolio
|   |-- main.py           # CLI report generator
|   `-- requirements.txt  # Python dependencies
|-- frontend/             # Dashboard applications
|   |-- streamlit/        # Streamlit dashboard
|   `-- nextjs/           # Optional Next.js dashboard scaffold
|-- docs/                 # Project guide and interview notes
|-- images/               # Generated charts and screenshots
|-- notebooks/            # Jupyter exploratory analysis
|-- outputs/              # Generated analysis CSV files
|-- reports/              # Generated Markdown reports
`-- README.md
```

## Installation

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r backend/requirements.txt
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## How To Run

Generate a report:

```bash
python -m backend.main --ticker AAPL --start 2020-01-01
```

Run the API:

```bash
python -m uvicorn backend.api.app:app --reload
```

Run the Streamlit dashboard:

```bash
python -m streamlit run frontend/streamlit/app.py
```

Open:

```text
API docs:  http://127.0.0.1:8000/docs
Dashboard: http://127.0.0.1:8501
```

## Main API Endpoints

- `GET /market/overview` - market breadth, top gainers, top losers
- `GET /glossary` - finance and technology full forms
- `GET /live/{ticker}` - simulated live price snapshot
- `GET /chart/{ticker}` - OHLCV and indicator chart data
- `GET /analytics/{ticker}` - signals, patterns, and risk metrics
- `GET /signals/{ticker}` - latest BUY/SELL/HOLD signal
- `POST /backtest/sma` - SMA crossover strategy backtest
- `POST /watchlist` and `GET /watchlist` - watchlist management
- `POST /portfolio/tx` and `GET /portfolio` - portfolio tracking
- `POST /alerts` and `POST /alerts/evaluate` - alert center
- `GET /news/{ticker}` - educational news and sentiment feed

## Advisor Review Mode

The dashboard includes an Advisor Review section for educational investment-research workflows. It asks for:

- Investment objective
- Time horizon
- Risk tolerance
- Liquidity need
- Investment experience
- Single-stock concentration limit

The system then compares those inputs with volatility, VaR (Value at Risk), maximum drawdown, and technical signals to produce educational review notes.

Important: this feature is not personalized financial advice. In real professional settings, investment recommendations require a complete customer profile, appropriate licensing/registration, conflict-of-interest controls, and suitability or fiduciary review depending on the service model and jurisdiction.

## Generated Outputs

- `outputs/{TICKER}_analysis_dataset.csv`
- `outputs/{TICKER}_summary.csv`
- `images/{TICKER}_closing_price.png`
- `images/{TICKER}_moving_averages.png`
- `images/{TICKER}_daily_returns.png`
- `images/{TICKER}_volatility.png`
- `reports/{TICKER}_analysis_report.md`

## Interview Explanation

I built a Python-based Stock Market Data Analyzer that fetches public OHLCV data, stores it in SQLite, computes technical indicators and risk metrics, generates BUY/SELL/HOLD signals, runs a vectorized SMA crossover backtest, exposes analytics through FastAPI, and visualizes market overview, technical analysis, portfolio, alerts, news sentiment, and backtesting results in a dashboard.

## Disclaimer

This project is for educational purposes and investment research simulation only. It does not provide regulated personalized financial advice, trading recommendations, or guaranteed financial results. Consult a qualified financial professional before making investment decisions.
