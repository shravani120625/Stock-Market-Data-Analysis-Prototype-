import sqlite3
import uuid
from datetime import datetime


def create_alert(db, ticker, rule, threshold):
    rule = rule.upper()
    if rule not in {"RSI_LT", "RSI_GT", "CLOSE_LT_BBLOWER", "CLOSE_GT_BBUPPER"}:
        raise ValueError("Unsupported rule")

    alert_id = str(uuid.uuid4())
    con = sqlite3.connect(db)
    con.execute(
        """
        INSERT INTO alerts(id, ticker, rule, threshold, active, last_fired)
        VALUES (?, ?, ?, ?, 1, NULL)
        """,
        (alert_id, ticker.upper(), rule, float(threshold)),
    )
    con.commit()
    con.close()
    return alert_id


def list_alerts(db="backend/db/market.db", active_only=True):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    sql = "SELECT * FROM alerts"
    if active_only:
        sql += " WHERE active=1"
    rows = con.execute(sql).fetchall()
    con.close()
    return [dict(row) for row in rows]


def evaluate_alerts(db="backend/db/market.db"):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    alerts = cur.execute("SELECT * FROM alerts WHERE active=1").fetchall()
    fired = []

    for alert in alerts:
        row = cur.execute(
            """
            SELECT c.date, c.close, i.rsi14, i.bb_lower, i.bb_upper
            FROM candles_daily c
            LEFT JOIN indicators_daily i ON i.ticker=c.ticker AND i.date=c.date
            WHERE c.ticker=?
            ORDER BY c.date DESC
            LIMIT 1
            """,
            (alert["ticker"],),
        ).fetchone()
        if not row:
            continue

        rule = alert["rule"]
        threshold = alert["threshold"]
        ok = (
            (rule == "RSI_LT" and row["rsi14"] is not None and row["rsi14"] < threshold)
            or (rule == "RSI_GT" and row["rsi14"] is not None and row["rsi14"] > threshold)
            or (rule == "CLOSE_LT_BBLOWER" and row["bb_lower"] is not None and row["close"] < row["bb_lower"])
            or (rule == "CLOSE_GT_BBUPPER" and row["bb_upper"] is not None and row["close"] > row["bb_upper"])
        )

        if ok:
            message = {
                "id": alert["id"],
                "ticker": alert["ticker"],
                "rule": rule,
                "date": row["date"],
                "close": row["close"],
                "rsi14": row["rsi14"],
            }
            fired.append(message)
            cur.execute(
                "UPDATE alerts SET last_fired=? WHERE id=?",
                (datetime.utcnow().isoformat(), alert["id"]),
            )

    con.commit()
    con.close()
    return fired
