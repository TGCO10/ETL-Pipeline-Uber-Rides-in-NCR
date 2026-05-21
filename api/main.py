from fastapi import FastAPI
import random
import time

app = FastAPI()

# ==============================
# Realtime metrics
# ==============================
@app.get("/realtime")
def realtime():

    return {
        "total_rides": random.randint(50, 500),
        "avg_fare": round(random.uniform(120, 450), 2)
    }

# ==============================
# Historical data
# ==============================
@app.get("/history")
def history():

    data = []

    now = int(time.time())

    for i in range(10):

        data.append({
            "window_start": str(now - i * 60),
            "window_end": str(now - (i - 1) * 60),
            "total_rides": random.randint(50, 500),
            "avg_fare": round(random.uniform(120, 450), 2)
        })

    return data

# ==============================
# Map data
# ==============================
@app.get("/map")
def map_data():

    routes = []

    for _ in range(5):

        path = []

        start_lat = random.uniform(28.45, 28.85)
        start_lon = random.uniform(76.9, 77.3)

        for i in range(20):

            path.append([
                start_lon + (i * 0.002),
                start_lat + (i * 0.001)
            ])

        routes.append({
            "path": path
        })

    return routes