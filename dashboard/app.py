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

# 🔥 YOUR RENDER API URL
API_BASE = "https://ride-analytics-api.onrender.com/"

# ==============================
# REALTIME METRICS
# ==============================
st.subheader("⚡ Real-Time Metrics")

col1, col2 = st.columns(2)

def fetch_realtime():

    try:
        response = requests.get(f"{API_BASE}/realtime")

        if response.status_code != 200:
            return {
                "total_rides": 0,
                "avg_fare": 0
            }

        data = response.json()

        return {
            "total_rides": data.get("total_rides", 0),
            "avg_fare": data.get("avg_fare", 0)
        }

    except Exception as e:

        st.error(str(e))

        return {
            "total_rides": 0,
            "avg_fare": 0
        }

realtime = fetch_realtime()

col1.metric(
    "Total Rides",
    realtime.get("total_rides", 0)
)

col2.metric(
    "Average Fare",
    realtime.get("avg_fare", 0)
)

# ==============================
# HISTORICAL DATA
# ==============================
st.subheader("📊 Historical Trends")

def fetch_history():

    try:

        response = requests.get(f"{API_BASE}/history")

        if response.status_code != 200:
            return pd.DataFrame()

        return pd.DataFrame(response.json())

    except:
        return pd.DataFrame()

df = fetch_history()

if not df.empty:

    if "window_start" in df.columns:

        df["window_start"] = pd.to_datetime(
            df["window_start"],
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

        response = requests.get(f"{API_BASE}/map")

        if response.status_code != 200:
            return []

        return response.json()

    except:
        return []

map_data = fetch_map()

if map_data:

    route_data = []

    for ride in map_data:

        # deployed API returns "path"
        if "path" in ride:

            route_data.append({
                "path": ride["path"]
            })

        # local API returns "route"
        elif "route" in ride:

            route_data.append({
                "path": ride["route"]
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