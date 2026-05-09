"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

type ChartRow = {
  date: string;
  close: number;
  sma20: number | null;
  sma50: number | null;
  rsi14: number | null;
};

type BacktestStats = {
  pnl: number;
  max_dd: number;
  sharpe: number;
  trades: number;
  win_rate: number;
};

export default function Home() {
  const [ticker, setTicker] = useState("AAPL");
  const [rows, setRows] = useState<ChartRow[]>([]);
  const [stats, setStats] = useState<BacktestStats | null>(null);
  const [status, setStatus] = useState("Ready");

  async function loadChart(symbol = ticker) {
    setStatus("Loading chart data...");
    const response = await fetch(`/api/chart/${symbol}?days=365`);
    const data = await response.json();
    setRows(data);
    setStatus(`Loaded ${data.length} rows for ${symbol}`);
  }

  async function refreshData() {
    setStatus("Refreshing data from backend...");
    await fetch(`/api/refresh/${ticker}`, { method: "POST" });
    await loadChart();
  }

  async function runBacktest() {
    setStatus("Running SMA backtest...");
    const response = await fetch("/api/backtest/sma", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker })
    });
    const data = await response.json();
    setStats(data.stats);
    setStatus("Backtest complete");
  }

  useEffect(() => {
    loadChart("AAPL");
  }, []);

  const latest = rows.at(-1);
  const previous = rows.at(-2);
  const change = latest && previous ? latest.close - previous.close : 0;

  return (
    <main className="page">
      <h1>Stock Market Data Analyzer</h1>
      <p className="muted">
        Watchlist charting, moving averages, RSI, and SMA strategy backtesting.
      </p>

      <section className="toolbar">
        <input
          value={ticker}
          onChange={(event) => setTicker(event.target.value.toUpperCase())}
          aria-label="Ticker symbol"
        />
        <button className="primary" onClick={() => loadChart()}>
          Load
        </button>
        <button className="primary" onClick={refreshData}>
          Refresh
        </button>
        <button className="success" onClick={runBacktest}>
          Backtest SMA
        </button>
        <span className="muted">{status}</span>
      </section>

      <section className="metrics">
        <div className="metric">
          <span>Latest Close</span>
          <strong>{latest ? `$${latest.close.toFixed(2)}` : "-"}</strong>
        </div>
        <div className="metric">
          <span>Daily Change</span>
          <strong>{change.toFixed(2)}</strong>
        </div>
        <div className="metric">
          <span>SMA 20</span>
          <strong>{latest?.sma20 ? latest.sma20.toFixed(2) : "-"}</strong>
        </div>
        <div className="metric">
          <span>RSI 14</span>
          <strong>{latest?.rsi14 ? latest.rsi14.toFixed(1) : "-"}</strong>
        </div>
      </section>

      <section className="panel">
        <h2>{ticker} Price Trend</h2>
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" minTickGap={28} />
            <YAxis domain={["auto", "auto"]} />
            <Tooltip />
            <Line type="monotone" dataKey="close" stroke="#2563eb" dot={false} />
            <Line type="monotone" dataKey="sma20" stroke="#059669" dot={false} />
            <Line type="monotone" dataKey="sma50" stroke="#dc2626" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </section>

      {stats && (
        <section className="panel">
          <h2>SMA20 &gt; SMA50 Backtest</h2>
          <p>
            PnL {(stats.pnl * 100).toFixed(1)}% | Max drawdown{" "}
            {(stats.max_dd * 100).toFixed(1)}% | Sharpe {stats.sharpe.toFixed(2)} |
            Trades {stats.trades} | Win rate {(stats.win_rate * 100).toFixed(1)}%
          </p>
        </section>
      )}
    </main>
  );
}
