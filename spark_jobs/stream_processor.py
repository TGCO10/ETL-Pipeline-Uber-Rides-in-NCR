from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, window, count, avg
from pyspark.sql.types import StructType, IntegerType, DoubleType, LongType
import redis
import json

# ==============================
# Schema
# ==============================
schema = StructType() \
    .add("ride_id", IntegerType()) \
    .add("driver_id", IntegerType()) \
    .add("user_id", IntegerType()) \
    .add("pickup_lat", DoubleType()) \
    .add("pickup_lon", DoubleType()) \
    .add("drop_lat", DoubleType()) \
    .add("drop_lon", DoubleType()) \
    .add("fare", DoubleType()) \
    .add("timestamp", LongType())

# ==============================
# Spark Session
# ==============================
spark = SparkSession.builder \
    .appName("RideStreamingProcessor") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ==============================
# Kafka Read
# ==============================
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "ride_events") \
    .option("startingOffsets", "latest") \
    .load()

# ==============================
# Parse JSON
# ==============================
json_df = df.selectExpr("CAST(value AS STRING)")

parsed_df = json_df.select(
    from_json(col("value"), schema).alias("data")
).select("data.*")

# ==============================
# Transform
# ==============================
processed_df = parsed_df \
    .withColumn("event_time", to_timestamp(col("timestamp"))) \
    .withColumn("fare_per_km", col("fare") / 10)

# ==============================
# Aggregation
# ==============================
agg_df = processed_df \
    .groupBy(window(col("event_time"), "1 minute")) \
    .agg(
        count("*").alias("total_rides"),
        avg("fare").alias("avg_fare")
    )

# ==============================
# Write Aggregates (Postgres + Redis)
# ==============================
def write_aggregates(batch_df, batch_id):
    final_df = batch_df.select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("total_rides"),
        col("avg_fare")
    )

    # PostgreSQL
    final_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/rides_db") \
        .option("dbtable", "ride_metrics") \
        .option("user", "admin") \
        .option("password", "admin") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

    # Redis (metrics)
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    rows = final_df.collect()

    for row in rows:
        r.set("latest_total_rides", row["total_rides"])
        r.set("latest_avg_fare", float(row["avg_fare"]))


# ==============================
# Write Raw Locations (Redis)
# ==============================
def write_locations(batch_df, batch_id):
    r = redis.Redis(host="redis", port=6379, decode_responses=True)

    rows = batch_df.select("pickup_lat", "pickup_lon").limit(50).collect()

    locations = [
        {"lat": row["pickup_lat"], "lon": row["pickup_lon"]}
        for row in rows
    ]

    r.set("latest_locations", json.dumps(locations))


# ==============================
# Streaming Queries
# ==============================
agg_query = agg_df.writeStream \
    .outputMode("complete") \
    .foreachBatch(write_aggregates) \
    .start()

raw_query = processed_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_locations) \
    .start()

agg_query.awaitTermination()