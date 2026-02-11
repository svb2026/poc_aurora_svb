# Script autonome de collecte toutes les 2 minutes pour plusieurs webcams
# Remplit le CSV avec l'intensité moyenne du vert et le score d'intensité

import pandas as pd
from datetime import datetime
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import time as t

CSV_FILE = "aurora_multi_webcams.csv"
webcams = {
    "NR3 West view": "https://uk.jokkmokk.jp/photo/nr3/latest.jpg",
    "NR4 North view": "https://uk.jokkmokk.jp/photo/nr4/latest.jpg",
    "Apukka Resort Rovaniemi": "https://youtu.be/bOEvPL206Hc"
}

# Charger le CSV existant ou créer un nouveau
try:
    df_global = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    df_global = pd.DataFrame(columns=['timestamp','camera','green_mean','green_score'])

while True:
    for name, url in webcams.items():
        try:
            response = requests.get(url, timeout=2)
            img = Image.open(BytesIO(response.content))
            arr = np.array(img)
            green_mean, green_score = 0, 0
            if arr.ndim == 3 and arr.shape[2] >= 3:
                green_channel = arr[:,:,1]
                green_mean = np.mean(green_channel)
                if green_mean < 10: green_score=0
                elif green_mean < 50: green_score=1
                elif green_mean < 100: green_score=2
                elif green_mean < 150: green_score=3
                elif green_mean < 200: green_score=4
                else: green_score=5

            new_row = {
                'timestamp': datetime.now().isoformat(),
                'camera': name,
                'green_mean': green_mean,
                'green_score': green_score
            }
            df_global = pd.concat([df_global, pd.DataFrame([new_row])], ignore_index=True)
            df_global.to_csv(CSV_FILE, index=False)
            print(f"Mesure enregistrée pour {name} à {new_row['timestamp']}")
        except Exception as e:
            print(f"Erreur pour {name}: {e}")

    t.sleep(600)  # attendre 2 minutes avant la prochaine collecte
