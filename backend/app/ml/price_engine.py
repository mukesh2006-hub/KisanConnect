from pathlib import Path
import pandas as pd
import numpy as np

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "tomato_prices.csv"

def _load_data():
    return pd.read_csv(DATA_PATH, parse_dates=["date"])

def _fallback_prediction(df):
    df = df.sort_values("date")
    recent = df.tail(7)["modal_price"].astype(float)
    current = float(recent.iloc[-1])
    previous = float(recent.iloc[0])
    trend = ((current - previous) / previous * 100) if previous else 0
    predicted = current * (1 + trend / 100 / 7)
    return predicted, trend

def _prophet_prediction(df):
    try:
        from prophet import Prophet
    except Exception:
        return None

    train = df[["date", "modal_price"]].rename(columns={"date": "ds", "modal_price": "y"})
    if len(train) < 14:
        return None

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
    )
    model.fit(train)
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    predicted = float(forecast.iloc[-7]["yhat"])
    return predicted

def recommend_price(crop="Tomato", market="Kolar", quality="Grade A", quantity=500):
    df = _load_data()
    df = df[(df["crop"].str.lower() == crop.lower()) & (df["market"].str.lower() == market.lower())]
    if df.empty:
        df = _load_data()

    current = float(df.sort_values("date").iloc[-1]["modal_price"])
    fallback_pred, trend = _fallback_prediction(df)

    predicted = _prophet_prediction(df)
    model_name = "Prophet" if predicted is not None else "7-day trend fallback"
    if predicted is None:
        predicted = fallback_pred

    quality_adj = {"Grade A": 1.0, "Grade B": 0.0, "Grade C": -1.0}.get(quality, 0.0)
    demand = "HIGH" if trend >= 3 else ("MEDIUM" if trend >= -2 else "LOW")
    demand_adj = {"HIGH": 1.5, "MEDIUM": 0.5, "LOW": -0.5}[demand]

    recommended = round(max(1, 0.45 * current + 0.55 * predicted + quality_adj + demand_adj), 2)
    min_price = round(max(1, recommended - 2), 2)
    max_price = round(recommended + 2, 2)

    explanation = [
        f"Current mandi modal price: ₹{current:.0f}/kg",
        f"Recent 7-day trend: {trend:+.1f}%",
        f"Near-term model estimate: ₹{predicted:.0f}/kg",
        f"Demand signal: {demand}",
        f"Quality adjustment: {quality_adj:+.0f} ₹/kg",
    ]

    return {
        "recommended_price": recommended,
        "min_price": min_price,
        "max_price": max_price,
        "current_mandi_price": round(current, 2),
        "predicted_price": round(predicted, 2),
        "demand": demand,
        "trend_percent": round(trend, 2),
        "explanation": explanation,
        "model": model_name,
    }
