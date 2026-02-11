# Collecte structurée avec stockage parquet exploitable

import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime, timezone
import os
import time

OUTPUT_FILE = "aurora_dataset.parquet"

CAMERAS = {
    "NR3 West view": {
        "url": "https://uk.jokkmokk.jp/photo/nr3/latest.jpg",
        "lat": 66.6,
        "lon": 19.8
    },
    "NR4 North view": {
        "url": "https://uk.jokkmokk.jp/photo/nr4/latest.jpg",
        "lat": 66.6,
        "lon": 19.8
    }
}

def compute_intensity(img):
    arr = np.array(img).astype(float)
    green = arr[:,:,1]
    red = arr[:,:,0]
    blue = arr[:,:,2]

    signal = np.clip(green - (red + blue)/2, 0, None)
    luminance = np.mean(arr)

    norm_intensity = np.mean(signal) / (luminance + 1e-6)
    return float(norm_intensity)

def get_kp():
    try:
        r = requests.get(
            "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
            timeout=5
        )
        return float(r.json()[-1][1])
    except:
        return np.nan

while True:
    rows = []
    kp = get_kp()

    for name, meta in CAMERAS.items():
        try:
            r = requests.get(meta["url"], timeout=5)
            img = Image.open(BytesIO(r.content)).convert("RGB")

            intensity = compute_intensity(img)

            rows.append({
                "timestamp_utc": datetime.now(timezone.utc),
                "camera": name,
                "lat": meta["lat"],
                "lon": meta["lon"],
                "kp": kp,
                "intensity": intensity
            })

            print(f"OK {name} | Intensity={intensity:.4f}")

        except Exception as e:
            print(f"Erreur {name}: {e}")

    if rows:
        df_new = pd.DataFrame(rows)

        if os.path.exists(OUTPUT_FILE):
            df_old = pd.read_parquet(OUTPUT_FILE)
            df_all = pd.concat([df_old, df_new])
        else:
            df_all = df_new

        df_all.to_parquet(OUTPUT_FILE, index=False)

    time.sleep(600)

