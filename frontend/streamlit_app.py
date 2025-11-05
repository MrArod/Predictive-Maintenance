"""Streamlit dashboard for turbine predictive maintenance insights."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_BASE_URL = os.getenv("PREDICTIVE_API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("PREDICTIVE_API_KEY", "dev-secret")
REQUEST_TIMEOUT = int(os.getenv("PREDICTIVE_API_TIMEOUT", "10"))


def _headers() -> Dict[str, str]:
    return {"X-API-Key": API_KEY}


@st.cache_data(ttl=30)
def fetch_predictions(engine_id: Optional[str] = None) -> Dict:
    params = {"engine_id": engine_id} if engine_id else {}
    response = requests.get(
        f"{API_BASE_URL}/predict", params=params, headers=_headers(), timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=30)
def fetch_metrics(engine_id: Optional[str] = None) -> Dict:
    params = {"engine_id": engine_id} if engine_id else {}
    response = requests.get(
        f"{API_BASE_URL}/metrics", params=params, headers=_headers(), timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def _format_timestamp(timestamp: str) -> str:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")


def render_kpi_cards(aggregates: Dict[str, float]) -> None:
    st.subheader("Key Performance Indicators")
    cols = st.columns(5)
    cols[0].metric("Production Efficiency", f"{aggregates['production_efficiency']:.1f}%")
    cols[1].metric("Failure Rate", f"{aggregates['failure_rate']:.1f}%")
    cols[2].metric("MTTF", f"{aggregates['mean_time_to_failure']:.0f} cycles")
    cols[3].metric("Average RUL", f"{aggregates['average_rul']:.0f} cycles")
    cols[4].metric("Downtime Cost", f"${aggregates['downtime_cost']:,.0f}/hr")


def render_engine_alerts(engines: List[Dict]) -> None:
    critical = [e for e in engines if e["failure_probability"] >= 0.35]
    warning = [e for e in engines if 0.2 <= e["failure_probability"] < 0.35]

    if critical:
        names = ", ".join(e["engine_id"] for e in critical)
        st.error(f"⚠️ Critical failure risk detected for: {names}")
    if warning:
        names = ", ".join(e["engine_id"] for e in warning)
        st.warning(f"⚠️ Elevated failure probability for: {names}")
    if not critical and not warning:
        st.success("All monitored engines are operating within acceptable thresholds.")


def render_engine_trends(trends: List[Dict], engine_id: Optional[str]) -> None:
    if not trends:
        st.info("No trend data available for the selected engine yet.")
        return

    df = pd.DataFrame(trends)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    title_suffix = f" - Engine {engine_id}" if engine_id else " - Fleet"

    fig_rul = px.line(
        df,
        x="timestamp",
        y="rul",
        color="engine_id",
        markers=True,
        title=f"Remaining Useful Life Trend{title_suffix}",
    )
    fig_rul.update_layout(yaxis_title="RUL (cycles)")

    fig_failure = px.line(
        df,
        x="timestamp",
        y="failure_probability",
        color="engine_id",
        markers=True,
        title=f"Failure Probability Trend{title_suffix}",
    )
    fig_failure.update_layout(yaxis_title="Failure Probability", yaxis_tickformat=".0%")

    st.plotly_chart(fig_rul, use_container_width=True)
    st.plotly_chart(fig_failure, use_container_width=True)


def render_kpi_trends(trends: List[Dict]) -> None:
    if not trends:
        return

    df = pd.DataFrame(trends)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for metric, metric_df in df.groupby("metric"):
        fig = px.line(
            metric_df,
            x="timestamp",
            y="value",
            markers=True,
            title=f"{metric.replace('_', ' ').title()} Trend",
        )
        st.plotly_chart(fig, use_container_width=True)


st.set_page_config(page_title="Predictive Maintenance Dashboard", layout="wide")
st.title("Turbine Health & KPI Overview")

st.sidebar.header("Configuration")
st.sidebar.write(f"API Base URL: {API_BASE_URL}")

try:
    metrics_data = fetch_metrics()
    predict_data = fetch_predictions()
except requests.HTTPError as exc:
    st.error(f"API responded with an error: {exc}")
    st.stop()
except requests.RequestException as exc:
    st.error(f"Unable to reach the API endpoint: {exc}")
    st.stop()

engines = predict_data.get("engines", [])
engine_options = ["All engines"] + [engine["engine_id"] for engine in engines]
selected_engine = st.sidebar.selectbox("Select Engine", engine_options)

if selected_engine != "All engines":
    metrics_data = fetch_metrics(selected_engine)
    predict_data = fetch_predictions(selected_engine)
    engines = predict_data.get("engines", [])

st.caption(f"Last updated: {_format_timestamp(metrics_data['generated_at'])}")

render_engine_alerts(engines)
render_kpi_cards(metrics_data["aggregates"])

st.subheader("Engine Performance")
render_engine_trends(
    metrics_data.get("engine_trends", []), None if selected_engine == "All engines" else selected_engine
)

st.subheader("Fleet KPI Trends")
render_kpi_trends(metrics_data.get("kpi_trends", []))

st.subheader("Engine Snapshot")
if engines:
    engine_df = pd.DataFrame(engines)
    engine_df["timestamp"] = pd.to_datetime(engine_df["timestamp"]).dt.tz_localize(None)
    st.dataframe(engine_df.set_index("engine_id"))
else:
    st.info("No engine predictions found for the selected filter.")
