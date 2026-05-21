import json
import time
import random
import requests
from kafka import KafkaProducer
from config import KAFKA_BROKER, TOPIC_NAME

# ==============================
# Kafka Producer
# ==============================
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# ==============================
# Delhi Bounding Box
# ==============================
DELHI_BOUNDS = {
    "min_lat": 28.40,
    "max_lat": 28.90,
    "min_lon": 76.85,
    "max_lon": 77.35
}

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjMyNWVhOTcyZTFlYzRhMmVhYzVlMGM4MDU3NjA4MDZkIiwiaCI6Im11cm11cjY0In0="

# ==============================
# Generate random Delhi point
# ==============================
def random_location():
    return (
        random.uniform(DELHI_BOUNDS["min_lon"], DELHI_BOUNDS["max_lon"]),
        random.uniform(DELHI_BOUNDS["min_lat"], DELHI_BOUNDS["max_lat"])
    )

# ==============================
# Get realistic route
# ==============================
def get_route(start, end):

    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [start[0], start[1]],
            [end[0], end[1]]
        ]
    }

    try:
        response = requests.post(url, json=body, headers=headers)

        data = response.json()

        # 🔥 SAFETY CHECK
        if "routes" not in data:
            print("❌ Route API failed")
            print(data)
            return None, None

        coords = data["routes"][0]["geometry"]

        decoded = decode_polyline(coords)

        distance_km = data["routes"][0]["summary"]["distance"] / 1000

        return decoded, distance_km

    except Exception as e:
        print("❌ Routing Error:", e)
        return None, None

# ==============================
# Polyline Decoder
# ==============================
def decode_polyline(polyline_str):

    index, lat, lng = 0, 0, 0
    coordinates = []

    while index < len(polyline_str):

        shift, result = 0, 0

        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        shift, result = 0, 0

        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        coordinates.append([lng / 1e5, lat / 1e5])

    return coordinates

# ==============================
# Simulate Ride
# ==============================
def simulate_ride():

    start = random_location()
    end = random_location()

    route, distance = get_route(start, end)

    if not route:
        return

    ride_id = random.randint(1000, 9999)
    driver_id = random.randint(1, 500)
    user_id = random.randint(1000, 5000)

    base_fare = 50
    fare_per_km = random.uniform(12, 25)

    fare = round(base_fare + (distance * fare_per_km), 2)

    for point in route:

        ride = {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "user_id": user_id,

            "pickup_lat": point[1],
            "pickup_lon": point[0],

            "drop_lat": end[1],
            "drop_lon": end[0],

            "route": route,

            "fare": fare,
            "timestamp": int(time.time())
        }

        producer.send(TOPIC_NAME, ride)

        print("🚖 Ride Update:", ride)

        time.sleep(1)

# ==============================
# Main Loop
# ==============================
def main():

    print("🚖 Uber-like Ride Simulation Started...")

    while True:
        simulate_ride()

if __name__ == "__main__":
    main()