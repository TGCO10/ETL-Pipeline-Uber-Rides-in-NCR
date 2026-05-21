import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import time

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="Ride Analytics Dashboard",
    layout="wide"
)

st.title("🚖 Real-Time Ride Analytics Dashboard")

# 🔥 FIXED API URL
API_BASE = "https://ride-analytics-api.onrender.com"

# ==============================
# REALTIME METRICS
# ==============================
st.subheader("⚡ Real-Time Metrics")

col1, col2 = st.columns(2)

def fetch_realtime():

    try:
        response = requests.get(
            f"{API_BASE}/realtime",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "total_rides": data.get("total_rides", 0),
            "avg_fare": data.get("avg_fare", 0)
        }

    except Exception as e:

        st.error(f"Realtime API Error: {e}")

        return {
            "total_rides": 0,
            "avg_fare": 0
        }

realtime = fetch_realtime()

col1.metric(
    "Total Rides",
    realtime["total_rides"]
)

col2.metric(
    "Average Fare",
    f"₹{realtime['avg_fare']}"
)

# ==============================
# HISTORICAL DATA
# ==============================
st.subheader("📊 Historical Trends")

def fetch_history():

    try:

        response = requests.get(
            f"{API_BASE}/history",
            timeout=10
        )

        response.raise_for_status()

        return pd.DataFrame(response.json())

    except Exception as e:

        st.error(f"History API Error: {e}")

        return pd.DataFrame()

df = fetch_history()

if not df.empty:

    df["window_start"] = pd.to_datetime(
        df["window_start"],
        unit="s",
        errors="coerce"
    )

    st.line_chart(
        df.set_index("window_start")["total_rides"]
    )

    st.line_chart(
        df.set_index("window_start")["avg_fare"]
    )

    st.dataframe(df)

else:
    st.warning("No historical data available.")

# ==============================
# LIVE ROUTE MAP
# ==============================
st.subheader("🗺️ Live Ride Routes")

def fetch_map():

    try:

        response = requests.get(
            f"{API_BASE}/map",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        st.error(f"Map API Error: {e}")

        return []

map_data = fetch_map()

if map_data:

    route_data = []

    for ride in map_data:

        if "path" in ride:

            route_data.append({
                "path": ride["path"]
            })

    if route_data:

        path_layer = pdk.Layer(
            "PathLayer",
            data=route_data,
            get_path="path",
            get_width=5,
            width_min_pixels=2,
            pickable=True
        )

        view_state = pdk.ViewState(
            latitude=28.6139,
            longitude=77.2090,
            zoom=9,
            pitch=45
        )

        deck = pdk.Deck(
            layers=[path_layer],
            initial_view_state=view_state,
            map_provider="carto",
            map_style="light"
        )

        st.pydeck_chart(deck)

    else:
        st.warning("No valid routes available.")

else:
    st.warning("No map data available.")

# ==============================
# AUTO REFRESH
# ==============================
time.sleep(5)
st.rerun()