import json
import time
import random
import requests
import polyline
from kafka import KafkaProducer
from config import KAFKA_BROKER, TOPIC_NAME

# 🔑 Add your OpenRouteService API key
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjMyNWVhOTcyZTFlYzRhMmVhYzVlMGM4MDU3NjA4MDZkIiwiaCI6Im11cm11cjY0In0="

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ==============================
# Delhi Bounding Box
# ==============================
DELHI_BOUNDS = {
    "lat_min": 28.40,
    "lat_max": 28.90,
    "lon_min": 76.80,
    "lon_max": 77.40
}

def random_location():
    return [
        random.uniform(DELHI_BOUNDS["lon_min"], DELHI_BOUNDS["lon_max"]),
        random.uniform(DELHI_BOUNDS["lat_min"], DELHI_BOUNDS["lat_max"])
    ]

# ==============================
# Get route from ORS
# ==============================
def get_route(start, end):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [start, end]
    }

    try:
        res = requests.post(url, json=body, headers=headers)

        if res.status_code != 200:
            print("❌ API Error:", res.text)
            return None, None

        data = res.json()

        # ✅ Handle ORS format (routes + encoded geometry)
        if "routes" in data:
            route_data = data["routes"][0]

            coords = polyline.decode(route_data["geometry"])  # [(lat, lon)]
            distance = route_data["summary"]["distance"]

            # convert → [lon, lat] format
            coords = [[lon, lat] for lat, lon in coords]

            return coords, distance

        # fallback (rare)
        elif "features" in data:
            coords = data["features"][0]["geometry"]["coordinates"]
            distance = data["features"][0]["properties"]["summary"]["distance"]
            return coords, distance

        else:
            print("❌ Unknown response:", data)
            return None, None

    except Exception as e:
        print("❌ Exception:", str(e))
        return None, None

# ==============================
# Simulate ride
# ==============================
def simulate_ride():
    start = random_location()
    end = random_location()

    route, distance = get_route(start, end)

    if not route or not distance:
        return

    ride_id = random.randint(1000, 9999)
    driver_id = random.randint(1, 100)
    user_id = random.randint(100, 500)

    fare = round(distance * 0.02, 2)

    for point in route[::5]:  # smooth movement
        ride = {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "user_id": user_id,
            "pickup_lat": point[1],
            "pickup_lon": point[0],
            "drop_lat": end[1],
            "drop_lon": end[0],
            "fare": fare,
            "timestamp": int(time.time())
        }

        print("🚗 Sending:", ride)
        producer.send(TOPIC_NAME, ride)

        time.sleep(0.5)

# ==============================
# Main
# ==============================
def main():
    print("🚖 Uber-like Ride Simulation Started...")

    while True:
        simulate_ride()
        time.sleep(1)  # avoid rate limit

if __name__ == "__main__":
    main()