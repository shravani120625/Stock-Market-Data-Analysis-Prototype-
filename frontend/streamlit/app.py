import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Stock Market Data Analyzer",
    page_icon="chart",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; }
    div[data-testid="stTabs"] button { font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Stock Market Data Analyzer")
st.caption(
    "Market data, technical indicators, trading signals, portfolio analytics, risk metrics, "
    "backtesting, alerts, and news sentiment. Educational project only, not financial advice."
)

st.sidebar.header("Controls")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
live_mode = st.sidebar.checkbox("Auto refresh every 30 seconds", value=False)
refresh_btn = st.sidebar.button("Refresh Market Data")


def api_get(path):
    response = requests.get(f"{API_URL}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


def api_post(path, payload=None):
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


if refresh_btn:
    with st.spinner(f"Fetching latest data for {ticker}..."):
        api_post(f"/refresh/{ticker}")
    st.success(f"{ticker} refreshed")


@st.cache_data(ttl=60)
def fetch_chart_data(symbol):
    return api_get(f"/chart/{symbol}?days=365")


@st.cache_data(ttl=60)
def fetch_analytics(symbol):
    return api_get(f"/analytics/{symbol}")


try:
    chart_data = fetch_chart_data(ticker)
    analytics = fetch_analytics(ticker)
    live = api_get(f"/live/{ticker}")
    df = pd.DataFrame(chart_data)
except Exception as exc:
    st.error(f"API connection error: {exc}")
    st.info("Start the backend with: python -m uvicorn backend.api.app:app --reload")
    st.stop()

if df.empty:
    st.warning("No chart data found. Click refresh or choose another ticker.")
    st.stop()

tabs = st.tabs(
    [
        "Executive Summary",
        "Market Overview",
        "Technical Analysis",
        "Signals & Watchlist",
        "Portfolio Analytics",
        "Advisor Review",
        "Backtesting Lab",
        "News Sentiment",
        "Alerts Center",
    ]
)

with tabs[0]:
    st.subheader("Live Market Snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price", f"${live['price']:,.2f}", f"{live['day_change_pct']:.2f}%")
    c2.metric("Bid / Ask", f"{live['bid']:.2f} / {live['ask']:.2f}")
    c3.metric("Day High / Low", f"{live['day_high']:.2f} / {live['day_low']:.2f}")
    c4.metric("Volume", f"{live['volume']:,}")
    st.caption(
        "Bid is the best buyer price, Ask is the best seller price, and Volume is the number "
        "of traded units. This live panel is simulated from the latest available public candle."
    )

    fig_main = go.Figure()
    fig_main.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLCV Candle",
        )
    )
    fig_main.add_trace(go.Scatter(x=df["date"], y=df["sma20"], name="SMA 20 - Simple Moving Average"))
    fig_main.add_trace(go.Scatter(x=df["date"], y=df["sma50"], name="SMA 50 - Simple Moving Average"))
    fig_main.update_layout(
        title="OHLCV - Open, High, Low, Close, Volume Price Action",
        height=520,
        margin=dict(l=0, r=0, t=45, b=0),
    )
    st.plotly_chart(fig_main, use_container_width=True)

with tabs[1]:
    st.subheader("Market Breadth Overview")
    overview = api_get("/market/overview")
    b1, b2, b3 = st.columns(3)
    b1.metric("Tracked Symbols", overview["count"])
    b2.metric("Advancing", overview["advance_decline"]["advancing"])
    b3.metric("Declining", overview["advance_decline"]["declining"])
    st.caption("Market breadth compares advancing symbols versus declining symbols in the local watch universe.")

    g_col, l_col = st.columns(2)
    with g_col:
        st.subheader("Top Gainers")
        st.dataframe(pd.DataFrame(overview["top_gainers"]), use_container_width=True)
    with l_col:
        st.subheader("Top Losers")
        st.dataframe(pd.DataFrame(overview["top_losers"]), use_container_width=True)

with tabs[2]:
    st.subheader("Technical Indicator Stack")
    col_ind1, col_ind2 = st.columns([2, 1])
    with col_ind1:
        fig_rsi = px.line(df, x="date", y="rsi14", title="RSI - Relative Strength Index (14 Periods)")
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        st.plotly_chart(fig_rsi, use_container_width=True)

        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df["date"], y=df["macd"], name="MACD Line"))
        fig_macd.add_trace(go.Scatter(x=df["date"], y=df["macd_signal"], name="MACD Signal Line"))
        fig_macd.update_layout(title="MACD - Moving Average Convergence Divergence", height=320)
        st.plotly_chart(fig_macd, use_container_width=True)

    with col_ind2:
        st.subheader("Candlestick Patterns")
        if analytics["patterns"]:
            for pattern in analytics["patterns"]:
                st.success(pattern)
        else:
            st.info("No major candlestick pattern detected.")

        st.subheader("Risk Metrics")
        risk_rows = [
            {"Metric": "Volatility", "Full Form": "Annualized Volatility", "Value": analytics["risk"]["volatility"]},
            {"Metric": "VaR", "Full Form": "Value at Risk", "Value": analytics["risk"]["var_95"]},
            {"Metric": "Max DD", "Full Form": "Maximum Drawdown", "Value": analytics["risk"]["max_drawdown"]},
            {"Metric": "Sharpe", "Full Form": "Sharpe Ratio", "Value": analytics["risk"]["sharpe"]},
            {"Metric": "Beta", "Full Form": "Market Beta", "Value": analytics["risk"]["beta"]},
            {"Metric": "Alpha", "Full Form": "Excess Return Alpha", "Value": analytics["risk"]["alpha"]},
        ]
        st.dataframe(pd.DataFrame(risk_rows), use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Trading Signal Engine")
    signal = api_get(f"/signals/{ticker}")
    s1, s2, s3 = st.columns(3)
    s1.metric("Signal", signal["signal"])
    s2.metric("Strength", f"{signal['strength'] * 100:.0f}%")
    s3.metric("Signal Date", signal["date"])
    st.info(signal["reason"])

    st.caption("Signals are generated from SMA, RSI, and MACD logic and should be treated as educational analysis, not trade advice.")

    st.subheader("Watchlist Management")
    with st.form("watchlist_form"):
        target = st.number_input("Target Price", min_value=0.0, value=float(live["price"] * 1.05))
        stop = st.number_input("Stop Loss", min_value=0.0, value=float(live["price"] * 0.95))
        if st.form_submit_button("Add To Watchlist"):
            api_post(
                "/watchlist",
                {"ticker": ticker, "name": "Default", "target_price": target, "stop_loss": stop},
            )
            st.success("Watchlist item saved")
    st.dataframe(pd.DataFrame(api_get("/watchlist")), use_container_width=True)

with tabs[4]:
    st.subheader("Portfolio Analytics")
    st.caption("PnL means Profit and Loss. Average cost is the average buy price of the position.")
    with st.form("tx_form"):
        c1, c2, c3, c4 = st.columns(4)
        side = c1.selectbox("Side", ["BUY", "SELL"])
        qty = c2.number_input("Quantity", min_value=0.0, value=1.0)
        price = c3.number_input("Price", min_value=0.0, value=float(live["price"]))
        fees = c4.number_input("Fees", min_value=0.0, value=0.0)
        if st.form_submit_button("Add Transaction"):
            api_post(
                "/portfolio/tx",
                {"ticker": ticker, "side": side, "qty": qty, "price": price, "fees": fees},
            )
            st.success("Transaction saved")

    portfolio = pd.DataFrame(api_get("/portfolio"))
    st.dataframe(portfolio, use_container_width=True)
    if not portfolio.empty and "market_value" in portfolio.columns:
        fig_alloc = px.pie(portfolio, values="market_value", names="ticker", title="Portfolio Allocation by Market Value")
        st.plotly_chart(fig_alloc, use_container_width=True)

with tabs[5]:
    st.subheader("Advisor Review - Educational Suitability Support")
    st.caption(
        "This section simulates the kind of investor-profile review used in professional workflows. "
        "It is not personalized financial advice and does not replace a licensed financial advisor."
    )

    p1, p2, p3 = st.columns(3)
    objective = p1.selectbox("Investment Objective", ["Capital Growth", "Income", "Capital Preservation"])
    horizon = p2.selectbox("Time Horizon", ["Short Term: under 1 year", "Medium Term: 1-5 years", "Long Term: 5+ years"])
    risk_tolerance = p3.selectbox("Risk Tolerance", ["Low", "Medium", "High"])

    p4, p5, p6 = st.columns(3)
    liquidity_need = p4.selectbox("Liquidity Need", ["Low", "Medium", "High"])
    experience = p5.selectbox("Investment Experience", ["Beginner", "Intermediate", "Advanced"])
    concentration = p6.slider("Single-Stock Concentration Limit (%)", min_value=5, max_value=100, value=25, step=5)

    risk = analytics["risk"]
    annual_volatility = risk["volatility"] * 100
    max_drawdown = risk["max_drawdown"] * 100
    var_95 = risk["var_95"] * 100

    a1, a2, a3 = st.columns(3)
    a1.metric("Volatility", f"{annual_volatility:.1f}%")
    a2.metric("VaR - Value at Risk", f"{var_95:.2f}%")
    a3.metric("Max DD - Maximum Drawdown", f"{max_drawdown:.1f}%")

    notes = []
    if risk_tolerance == "Low" and annual_volatility > 25:
        notes.append("Risk check: the selected symbol has high volatility relative to a low-risk profile.")
    if liquidity_need == "High" and horizon.startswith("Long"):
        notes.append("Profile check: high liquidity needs may conflict with a long-term investment horizon.")
    if objective == "Capital Preservation" and signal["signal"] == "SELL":
        notes.append("Signal check: current technical signal is defensive, which deserves extra review.")
    if experience == "Beginner":
        notes.append("Education check: review position sizing, diversification, and drawdown before acting.")
    if concentration < 20:
        notes.append("Concentration check: this profile prefers diversified exposure over a large single-stock position.")
    if not notes:
        notes.append("No major profile conflicts were detected by the educational rule engine.")

    st.subheader("Educational Review Notes")
    for note in notes:
        st.write(f"- {note}")

    st.warning(
        "This dashboard provides research signals and suitability-style educational checks only. "
        "It does not know your complete financial situation, tax status, liabilities, or legal constraints."
    )

with tabs[6]:
    st.subheader("SMA20/SMA50 Strategy Backtest")
    st.caption("SMA means Simple Moving Average. CAGR means Compound Annual Growth Rate.")
    if st.button("Run Vectorized Backtest"):
        bt = api_post("/backtest/sma", {"ticker": ticker})["stats"]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("CAGR", f"{bt['cagr'] * 100:.1f}%")
        c2.metric("Sharpe Ratio", f"{bt['sharpe']:.2f}")
        c3.metric("Max DD", f"{bt['max_dd'] * 100:.1f}%")
        c4.metric("Win Rate", f"{bt['win_rate'] * 100:.1f}%")
        c5.metric("Profit Factor", f"{bt['profit_factor']:.2f}")
        fig_bt = px.area(x=bt["dates"], y=bt["curve"], title="Equity Curve - Strategy Growth Simulation")
        st.plotly_chart(fig_bt, use_container_width=True)

with tabs[7]:
    st.subheader("News and Sentiment Monitor")
    st.caption("Sentiment labels classify headlines as Bullish, Bearish, or Neutral for educational analysis.")
    news = pd.DataFrame(api_get(f"/news/{ticker}"))
    st.dataframe(news, use_container_width=True)
    if not news.empty:
        counts = news["sentiment"].value_counts().reset_index()
        counts.columns = ["sentiment", "count"]
        st.plotly_chart(px.bar(counts, x="sentiment", y="count", title="Sentiment Mix"), use_container_width=True)

with tabs[8]:
    st.subheader("Alert Center")
    st.caption(
        "Supported rules: RSI_LT means Relative Strength Index less than threshold; "
        "RSI_GT means Relative Strength Index greater than threshold; "
        "CLOSE_LT_BBLOWER means close below lower Bollinger Band; "
        "CLOSE_GT_BBUPPER means close above upper Bollinger Band."
    )
    with st.form("alert_form"):
        rule = st.selectbox("Rule", ["RSI_LT", "RSI_GT", "CLOSE_LT_BBLOWER", "CLOSE_GT_BBUPPER"])
        threshold = st.number_input("Threshold", value=30.0)
        if st.form_submit_button("Create Alert"):
            api_post("/alerts", {"ticker": ticker, "rule": rule, "threshold": threshold})
            st.success("Alert created")

    if st.button("Evaluate Alerts Now"):
        st.json(api_post("/alerts/evaluate"))
    st.dataframe(pd.DataFrame(api_get("/alerts")), use_container_width=True)

if live_mode:
    time.sleep(30)
    st.rerun()
