import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from components.charts import line_price_chart

st.set_page_config(page_title="CryptoViz (skeleton)", layout="wide")

st.title("CryptoViz – Streamlit (squelette)")
st.caption("Demo UI légère – branchable sur Influx/Kafka ensuite")

# Sidebar controls
with st.sidebar:
    st.header("Filtres")
    cryptos = st.multiselect("Cryptos", ["bitcoin", "ethereum", "solana"], ["bitcoin", "ethereum", "solana"])
    hours = st.slider("Fenêtre (heures)", 1, 24, 6)

# Fake local dataset (placeholder)
end = datetime.utcnow()
start = end - timedelta(hours=hours)
idx = pd.date_range(start, end, freq="1min")

frames = []
for c in cryptos:
    y = np.cumsum(np.random.randn(len(idx))) + np.random.uniform(50, 400)
    frames.append(pd.DataFrame({"_time": idx, "_value": y, "crypto": c}))

df = pd.concat(frames, ignore_index=True)

st.subheader("price_usd (données factices)")
line_price_chart(df)

st.info(
    "Ce squelette charge des données factices. Prochaines étapes: lire Influx (bucket crypto-data) via influxdb-client, ou appeler l'API backend/Coingecko."
)
