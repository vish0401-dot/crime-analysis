from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.cluster import KMeans
import random

app = Flask(__name__)

# LOAD DATASET
df = pd.read_csv("data.csv")

# CLEAN COLUMN NAMES
df.columns = df.columns.str.strip().str.lower()

# RENAME IMPORTANT COLUMNS
df.rename(columns={
    "date of occurrence": "date",
    "city": "city"
}, inplace=True)

# FIX DATE FORMAT
df["date"] = pd.to_datetime(
    df["date"],
    format="%d-%m-%Y %H:%M",
    errors="coerce"
)

# CITY → BASE COORDINATES
city_coords = {
    "ahmedabad": (23.0225, 72.5714),
    "chennai": (13.0827, 80.2707),
    "ludhiana": (30.9000, 75.8573),
    "pune": (18.5204, 73.8567),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "kolkata": (22.5726, 88.3639),
     # 🔥 NEW CITIES
    "surat": (21.1702, 72.8311),
    "kanpur": (26.4499, 80.3319),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),
    "bhopal": (23.2599, 77.4126),
    "patna": (25.5941, 85.1376),
    "visakhapatnam": (17.6868, 83.2185),
    "coimbatore": (11.0168, 76.9558),
    "kochi": (9.9312, 76.2673),
    "thiruvananthapuram": (8.5241, 76.9366),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "meerut": (28.9845, 77.7064),
    "vadodara": (22.3072, 73.1812),
    "rajkot": (22.3039, 70.8022),
    "amritsar": (31.6340, 74.8723),
    "noida": (28.5355, 77.3910),
    "gurgaon": (28.4595, 77.0266)
}

# BASE COORDS
base_lat = df["city"].str.lower().map(
    lambda x: city_coords.get(x, (None, None))[0]
)

base_lon = df["city"].str.lower().map(
    lambda x: city_coords.get(x, (None, None))[1]
)

# CREATE DYNAMIC SPATIAL VARIATION
df["lat"] = base_lat + [
    random.uniform(-0.5, 0.5) for _ in range(len(df))
]

df["lon"] = base_lon + [
    random.uniform(-0.5, 0.5) for _ in range(len(df))
]

# REMOVE INVALID DATA
df = df.dropna(subset=["lat", "lon", "date"])

# CREATE SEASON
def get_season(m):
    if m in [12,1,2]:
        return "Winter"
    elif m in [3,4,5]:
        return "Summer"
    elif m in [6,7,8,9]:
        return "Monsoon"
    else:
        return "Winter"

df["season"] = df["date"].dt.month.apply(get_season)

# CREATE FESTIVAL
def get_festival(m):
    if m in [10,11]:
        return "Diwali"
    elif m in [3,4]:
        return "Holi"
    elif m in [4,5]:
        return "Eid"
    elif m == 12:
        return "Christmas"
    else:
        return "None"

df["festival"] = df["date"].dt.month.apply(get_festival)

# SEASONAL HOTSPOT MOVEMENT
df.loc[df["season"] == "Summer", "lat"] += 0.4

df.loc[df["season"] == "Winter", "lon"] += 0.4

df.loc[df["season"] == "Monsoon", "lat"] -= 0.4

# FESTIVAL EFFECT
df.loc[df["festival"] == "Diwali", "lon"] += 0.3

df.loc[df["festival"] == "Eid", "lat"] += 0.3

df.loc[df["festival"] == "Christmas", "lon"] -= 0.3

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cluster", methods=["POST"])
def cluster():

    data = request.json

    season = data.get("season")
    festival = data.get("festival")

    filtered = df.copy()

    # APPLY SEASON FILTER
    if season:
        filtered = filtered[
            filtered["season"].str.lower() == season.lower()
        ]

    # APPLY FESTIVAL FILTER
    if festival:
        temp = filtered[
            filtered["festival"].str.lower() == festival.lower()
        ]

        if len(temp) > 0:
            filtered = temp

    # FALLBACK
    if len(filtered) == 0:
        filtered = df.copy()

    coords = filtered[["lat", "lon"]]

    # KMEANS CLUSTERING
    if len(coords) < 3:
        filtered["cluster"] = 0
    else:
        k = min(3, len(coords))

        kmeans = KMeans(
            n_clusters=k,
            n_init=10,
            random_state=42
        )

        filtered["cluster"] = kmeans.fit_predict(coords)

    # CONVERT CLUSTERS → RISK LEVELS
    counts = (
        filtered["cluster"]
        .value_counts()
        .sort_values(ascending=False)
    )

    labels = ["High", "Medium", "Low"]

    risk_map = {}

    for i, cluster_id in enumerate(counts.index):

        if i < len(labels):
            risk_map[cluster_id] = labels[i]
        else:
            risk_map[cluster_id] = "Low"

    filtered["risk"] = filtered["cluster"].map(risk_map)

    filtered = filtered.fillna("")

    return jsonify(
        filtered.to_dict(orient="records")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
