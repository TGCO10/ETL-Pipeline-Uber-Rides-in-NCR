from fastapi import FastAPI
import redis
import psycopg2
import json

app = FastAPI()

# ==============================
# Redis
# ==============================
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

# ==============================
# PostgreSQL
# ==============================
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="rides_db",
    user="admin",
    password="admin"
)

# ==============================
# Realtime Metrics
# ==============================
@app.get("/realtime")
def get_realtime_metrics():

    total_rides = redis_client.get("latest_total_rides")
    avg_fare = redis_client.get("latest_avg_fare")

    return {
        "total_rides": total_rides,
        "avg_fare": avg_fare
    }

# ==============================
# History
# ==============================
@app.get("/history")
def get_history():

    cur = conn.cursor()

    cur.execute("""
        SELECT window_start,
               window_end,
               total_rides,
               avg_fare
        FROM ride_metrics
        ORDER BY window_start DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    return [
        {
            "window_start": str(r[0]),
            "window_end": str(r[1]),
            "total_rides": r[2],
            "avg_fare": float(r[3])
        }
        for r in rows
    ]

# ==============================
# Map Data
# ==============================
@app.get("/map")
def get_map():

    data = redis_client.get("latest_locations")

    if data:
        return json.loads(data)

    return []