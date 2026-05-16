import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Ride Analytics Dashboard", layout="wide")

st.title("🚖 Real-Time Ride Analytics Dashboard")

API_BASE = "http://127.0.0.1:8000"

# ==============================
# Real-time Metrics
# ==============================
st.subheader("⚡ Real-Time Metrics")

col1, col2 = st.columns(2)

def fetch_realtime():
    try:
        return requests.get(f"{API_BASE}/realtime").json()
    except:
        return {"total_rides": 0, "avg_fare": 0}

realtime = fetch_realtime()

col1.metric("Total Rides", realtime["total_rides"])
col2.metric("Avg Fare", realtime["avg_fare"])

# ==============================
# Map Visualization
# ==============================
st.subheader("🗺️ Live Ride Map")

def fetch_map():
    try:
        data = requests.get(f"{API_BASE}/map").json()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

map_df = fetch_map()

if not map_df.empty:
    map_df = map_df.rename(columns={"lat": "latitude", "lon": "longitude"})
    st.map(map_df)
else:
    st.warning("No map data available")

# ==============================
# Historical Trends
# ==============================
st.subheader("📊 Historical Trends")

def fetch_history():
    try:
        return pd.DataFrame(requests.get(f"{API_BASE}/history").json())
    except:
        return pd.DataFrame()

df = fetch_history()

if not df.empty:
    df["window_start"] = pd.to_datetime(df["window_start"])

    st.line_chart(df.set_index("window_start")["total_rides"])
    st.line_chart(df.set_index("window_start")["avg_fare"])
    st.dataframe(df)
else:
    st.warning("No historical data available")

# ==============================
# Auto-refresh
# ==============================
time.sleep(5)
st.rerun()