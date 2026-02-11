import streamlit as st
import pandas as pd
import numpy as np
import requests
import cv2
import yt_dlp
import urllib3
from PIL import Image, ImageDraw
from io import BytesIO
from datetime import datetime
from dataclasses import dataclass
from typing import List
import concurrent.futures
import pydeck as pdk

# Désactiver les alertes SSL pour les vieux sites de webcams
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# 1. CONFIGURATION & STRUCTURE DE DONNÉES
# =============================================================================
st.set_page_config(page_title="Aurora Network Pro", page_icon="🌌", layout="wide")

@dataclass
class AuroraCamera:
    id: str
    name: str
    country: str
    url: str
    lat: float
    lon: float

CAMERAS: List[AuroraCamera] = [
    # SUÈDE
    AuroraCamera("SE_KIRUNA", "Kiruna IRF", "🇸🇪 SWEDEN", "https://www.irf.se/alis/allsky/krn/latest.jpeg", 67.84, 20.41),
    AuroraCamera("SE_PORJUS", "Porjus Station", "🇸🇪 SWEDEN", "https://uk.jokkmokk.jp/photo/nr4/latest.jpg", 66.96, 19.81),
    AuroraCamera("SE_ABISKO", "Abisko Station", "🇸🇪 SWEDEN", "https://lightoverlapland.com/wp-content/uploads/webcam/abisko.jpg", 68.35, 18.82),
    AuroraCamera("YT_ABISKO", "Abisko (YouTube Live)", "🇸🇪 SWEDEN", "https://www.youtube.com/watch?v=TxMYSs1Qj8I", 68.35, 18.82),
    AuroraCamera("YT_LAPLAND", "Lapland Live", "🇸🇪 SWEDEN", "https://www.youtube.com/watch?v=TxMYSs1Qj8I", 68.35, 18.82),
    
    # FINLANDE
    AuroraCamera("POSIO", "Hotel_lapin_Satu", "🇫🇮 FINLAND", "https://www.youtube.com/live/iOmco6eIa-0?si=7JQbtJkn2gnfTeEj", 66.09, 28.13),
    AuroraCamera("FI_SODANKYLA", "Sodankylä Geo", "🇫🇮 FINLAND", "https://www.sgo.fi/Data/RealTime/AllSky/KR1/latest.jpg", 67.36, 26.63),
    AuroraCamera("YT_ROVANIEMI", "Rovaniemi Apukka", "🇫🇮 FINLAND", "https://www.youtube.com/watch?v=bOEvPL206Hc", 66.50, 25.72),
    
    # NORVÈGE
    AuroraCamera("NO_TROMSO", "Tromsø Sky", "🇳🇴 NORWAY", "http://weather.cs.uit.no/video/current.jpg", 69.64, 18.95),
    AuroraCamera("NO_SVALBARD", "Svalbard KHO", "🇳🇴 NORWAY", "http://kho.unis.no/quicklook/allsky_latest.jpg", 78.14, 16.04),
      
    # AMÉRIQUE
    AuroraCamera("CA_YELLOW", "Yellowknife CSA", "🇨🇦 CANADA", "https://auroramax.com/data/live/latest.jpg", 62.45, -114.37),
    AuroraCamera("US_ALASKA", "Fairbanks Poker Flat", "🇺🇸 ALASKA", "https://allsky.gi.alaska.edu/sites/default/files/cameras/poker/latest-sm.jpg", 64.83, -147.71),
]

# =============================================================================
# 2. FONCTIONS TECHNIQUES
# =============================================================================

def get_youtube_frame(youtube_url):
    """Extrait une image d'un flux YouTube Live."""
    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 8,
            'extractor_retries': 1
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_url = info['url']
        cap = cv2.VideoCapture(video_url)
        ret, frame = cap.read()
        cap.release()
        if ret:
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    except: return None
    return None

def create_placeholder(text="OFFLINE"):
    img = Image.new('RGB', (400, 300), color='#cbd5e1')
    d = ImageDraw.Draw(img)
    try: d.text((150, 140), text, fill=(100, 116, 139))
    except: pass
    return img

@st.cache_data(ttl=600)
def get_global_data():
    try:
        r = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3)
        return float(r.json()[-1][1])
    except: return 0.0

def fetch_camera_data(cam: AuroraCamera, kp_index: float):
    # 1. Météo via Open-Meteo
    weather = {"temp": "N/A", "clouds": 50}
    try:
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={cam.lat}&longitude={cam.lon}&current=temperature_2m,cloud_cover&timezone=auto"
        w_res = requests.get(w_url, timeout=5).json()
        weather = {"temp": round(w_res["current"]["temperature_2m"], 1), "clouds": w_res["current"]["cloud_cover"]}
    except: pass

    # 2. Image
    img = None
    status = "offline"
    intensity = 0.0
    try:
        if "youtu" in cam.url:
            img = get_youtube_frame(cam.url)
            if img: status = "online"
        else:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(cam.url, timeout=10, headers=headers, verify=False)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content)).convert("RGB")
                status = "online"

        if status == "online" and img:
            arr = np.array(img)
            green = arr[:,:,1].astype(float)
            blue_red = (arr[:,:,0].astype(float) + arr[:,:,2].astype(float)) / 2
            sig = np.clip(green - blue_red, 0, None)
            intensity = round(float(np.mean(sig)), 2)
        else:
            img = create_placeholder("OFFLINE")
    except:
        img = create_placeholder("ERROR")

    # 3. Probabilité
    clouds_factor = (100 - weather['clouds']) / 100
    score = min(5, int(intensity / 10))
    prob = int(max(0, min(100, (score * 25 + kp_index * 10 + (cam.lat - 55)) * clouds_factor)))

    return {"cam": cam, "img": img, "status": status, "prob": prob, "weather": weather, "intensity": intensity}

# =============================================================================
# 3. INTERFACE UTILISATEUR
# =============================================================================
st.title("🌌 Aurora Network Pro v2.0")
st.caption("Demarrage rapide: lancez le scan manuellement pour eviter le blocage au chargement.")

if "results" not in st.session_state:
    st.session_state["results"] = []

col_cfg_1, col_cfg_2 = st.columns([2, 1])
with col_cfg_1:
    scan_now = st.button("Scanner maintenant", type="primary")
with col_cfg_2:
    fast_mode = st.toggle("Mode rapide (sans YouTube)", value=True)

kp = get_global_data()
col1, col2 = st.columns(2)
col1.metric("Planetary K-Index", f"{kp} Kp")
col2.metric("Active Sensors", f"{len(CAMERAS)}")

if scan_now:
    cameras_to_scan = [c for c in CAMERAS if not (fast_mode and "youtu" in c.url.lower())]
    results = []
    with st.spinner("Scanning global network..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_camera_data, cam, kp) for cam in cameras_to_scan]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
    st.session_state["results"] = sorted(results, key=lambda x: x['prob'], reverse=True)

results = st.session_state["results"]

if not results:
    st.info("Aucun scan lance. Cliquez sur 'Scanner maintenant' pour charger les flux.")
    st.stop()

# Carte Pydeck
df_map = pd.DataFrame([{"lat": r["cam"].lat, "lon": r["cam"].lon, "prob": r["prob"], "name": r["cam"].name} for r in results])
st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(latitude=65, longitude=15, zoom=2),
    layers=[pdk.Layer("ScatterplotLayer", df_map, get_position='[lon, lat]', get_color='[255 - prob*2, prob*2.5, 100]', get_radius=80000)]
))

# Grille d'images
cols = st.columns(4)
for i, item in enumerate(results):
    with cols[i % 4]:
        st.markdown(f"**{item['cam'].name}** ({item['cam'].country})")
        st.image(item["img"], width='stretch')
        if item["status"] == "online":
            st.progress(item["prob"] / 100)
            # Remplacez l'ancienne ligne st.caption par celle-ci :
            st.caption(f"✨ Chance: {item['prob']}% | ☁️ Nuages: {item['weather']['clouds']}% | 📶 Intensité: {item['intensity']}")
        else:
            st.error("Feed unavailable")
