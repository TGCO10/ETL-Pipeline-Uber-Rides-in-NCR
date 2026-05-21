import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import time

st.set_page_config(
    page_title="Ride Analytics Dashboard",
    layout="wide"
)

st.title("🚖 Uber-Style Real-Time Ride Dashboard")

API_BASE = "http://127.0.0.1:8000"

# ==============================
# Realtime Metrics
# ==============================
st.subheader("⚡ Real-Time Metrics")

col1, col2 = st.columns(2)

def fetch_realtime():
    try:
        return requests.get(f"{API_BASE}/realtime").json()
    except:
        return {
            "total_rides": 0,
            "avg_fare": 0
        }

realtime = fetch_realtime()

col1.metric("Total Rides", realtime["total_rides"])
col2.metric("Average Fare", realtime["avg_fare"])

# ==============================
# Historical Trends
# ==============================
st.subheader("📊 Historical Trends")

def fetch_history():
    try:
        return pd.DataFrame(
            requests.get(f"{API_BASE}/history").json()
        )
    except:
        return pd.DataFrame()

df = fetch_history()

if not df.empty:

    df["window_start"] = pd.to_datetime(df["window_start"])

    st.line_chart(
        df.set_index("window_start")["total_rides"]
    )

    st.line_chart(
        df.set_index("window_start")["avg_fare"]
    )

    st.dataframe(df)

# ==============================
# Live Route Map
# ==============================
st.subheader("🗺️ Live Ride Routes")

def fetch_map():
    try:
        return requests.get(f"{API_BASE}/map").json()
    except Exception as e:
        st.error(str(e))
        return []

map_data = fetch_map()

if map_data:

    route_data = []

    for ride in map_data:

        route = ride.get("route")

        # ensure route exists and has enough points
        if route and len(route) > 1:

            route_data.append({
                "path": route
            })

    if route_data:

        # 🔥 Route layer
        path_layer = pdk.Layer(
            "PathLayer",
            data=route_data,
            get_path="path",
            get_width=5,
            width_min_pixels=2,
            pickable=True
        )

        # Delhi view
        view_state = pdk.ViewState(
            latitude=28.6139,
            longitude=77.2090,
            zoom=9,
            pitch=45
        )

        # 🔥 FINAL FIX
        deck = pdk.Deck(
            layers=[path_layer],
            initial_view_state=view_state,
            map_provider="carto",
            map_style="light"
        )

        st.pydeck_chart(deck)

    else:
        st.warning("No valid routes found.")

else:
    st.warning("No live route data available.")
        
# ==============================
# Auto Refresh
# ==============================
time.sleep(5)
st.rerun()