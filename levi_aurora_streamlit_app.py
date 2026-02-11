import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import pydeck as pdk

DATA_FILE = "aurora_dataset.parquet"

st.set_page_config(layout="wide")
st.title("Aurora Scientific Monitor")

@st.cache_data(ttl=300)
def load_data():
    try:
        return pd.read_parquet(DATA_FILE)
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data collected yet.")
    st.stop()

latest = df.sort_values("timestamp_utc").groupby("camera").tail(1)

st.subheader("Latest Intensities")

st.dataframe(latest[["camera", "kp", "intensity"]])

# Carte
df_map = latest.copy()
df_map["color"] = df_map["intensity"] * 255

deck = pdk.Deck(
    initial_view_state=pdk.ViewState(latitude=65, longitude=15, zoom=3),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            df_map,
            get_position='[lon, lat]',
            get_radius=50000,
            get_color='[color, 50, 200]'
        )
    ]
)

st.pydeck_chart(deck)

