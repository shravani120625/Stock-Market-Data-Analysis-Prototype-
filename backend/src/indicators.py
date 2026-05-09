import pandas as pd
import sqlite3
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

def compute_indicators(db="backend/db/market.db", ticker="AAPL"):
    con = sqlite3.connect(db)
    df = pd.read_sql_query(
        "SELECT date, close FROM candles_daily WHERE ticker=? ORDER BY date", 
        con, 
        params=[ticker]
    )
    
    if len(df) < 50:
        print(f"Not enough data for {ticker} indicators")
        con.close()
        return

    s = df["close"]
    
    # Calculate Indicators
    sma20 = SMAIndicator(s, window=20).sma_indicator()
    sma50 = SMAIndicator(s, window=50).sma_indicator()
    rsi14 = RSIIndicator(s, window=14).rsi()
    
    macd_obj = MACD(s)
    macd = macd_obj.macd()
    macd_sig = macd_obj.macd_signal()
    macd_hist = macd_obj.macd_diff()
    
    bb = BollingerBands(s, window=20, window_dev=2)
    
    out = pd.DataFrame({
        "date": df["date"],
        "sma20": sma20, 
        "sma50": sma50, 
        "rsi14": rsi14,
        "macd": macd, 
        "macd_signal": macd_sig, 
        "macd_hist": macd_hist,
        "bb_upper": bb.bollinger_hband(), 
        "bb_mid": bb.bollinger_mavg(), 
        "bb_lower": bb.bollinger_lband()
    }).dropna()
    
    cur = con.cursor()
    cur.executemany("""
        INSERT OR REPLACE INTO indicators_daily
        (ticker, date, sma20, sma50, rsi14, macd, macd_signal, macd_hist, bb_upper, bb_mid, bb_lower)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, [(ticker, *r) for r in out.itertuples(index=False, name=None)])
    
    con.commit()
    con.close()
    print(f"Computed indicators for {ticker}")

def detect_patterns(df):
    """Simple Candlestick Pattern Detection"""
    patterns = []
    if len(df) < 2: return patterns
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    body_size = abs(last['close'] - last['open'])
    upper_shadow = last['high'] - max(last['close'], last['open'])
    lower_shadow = min(last['close'], last['open']) - last['low']
    total_range = last['high'] - last['low']
    
    # 1. Doji
    if total_range > 0 and body_size / total_range < 0.1:
        patterns.append("Doji")
    
    # 2. Hammer
    if lower_shadow > 2 * body_size and upper_shadow < 0.1 * total_range:
        patterns.append("Hammer")
        
    # 3. Engulfing
    if prev['close'] < prev['open'] and last['close'] > last['open']:
        if last['close'] > prev['open'] and last['open'] < prev['close']:
            patterns.append("Bullish Engulfing")
            
    return patterns

def generate_signals(df):
    """Generate Buy/Sell signals based on indicators"""
    if len(df) < 2: return "HOLD", "Neutral"
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Simple Crossover Signal
    if prev['sma20'] < prev['sma50'] and last['sma20'] >= last['sma50']:
        return "BUY", "Golden Cross (SMA 20/50)"
    elif prev['sma20'] > prev['sma50'] and last['sma20'] <= last['sma50']:
        return "SELL", "Death Cross (SMA 20/50)"
        
    # RSI Signal
    if last['rsi14'] < 30:
        return "BUY", "RSI Oversold (<30)"
    elif last['rsi14'] > 70:
        return "SELL", "RSI Overbought (>70)"
        
    return "HOLD", "Wait for Trend"

if __name__ == "__main__":
    compute_indicators()
