import streamlit as st
from polygon import RESTClient
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# ---------- CONFIGURATION ----------
st.set_page_config(
    page_title="Tableau de bord Tendance & Valorisation",
    page_icon="📊",
    layout="centered"
)

API_KEY = st.secrets["polygon_api_key"]
client = RESTClient(API_KEY)

# ---------- FONCTIONS ----------

@st.cache_data(ttl=3600)
def get_polygon_data(ticker):
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=90)  # 3 mois

        aggs = client.get_aggs(
            ticker, 1, "day", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        data = pd.DataFrame(aggs)
        if not data.empty:
            data["date"] = pd.to_datetime(data["timestamp"], unit="ms")
            data.sort_values("date", inplace=True)
            return data
        else:
            return None
    except Exception as e:
        st.warning(f"Erreur pour {ticker} : {e}")
        return None

def analyze_data(df):
    close_price = df["close"].iloc[-1]
    ma50 = df["close"].rolling(window=50).mean().iloc[-1]
    ma200 = df["close"].rolling(window=200).mean().iloc[-1] if len(df) >= 200 else np.nan

    trend = "Haussière" if close_price > ma200 else "Baissière"
    cross = "Golden Cross ✅" if ma50 > ma200 else "Death Cross ❌"

    perf = (close_price / df["close"].iloc[-21] - 1) * 100 if len(df) > 21 else np.nan
    action = "Renforcer" if trend == "Haussière" else "Attendre"

    last_date = df["date"].max().strftime("%Y-%m-%d")
    return close_price, trend, cross, perf, action, last_date

# ---------- LISTE DES ACTIFS ----------
assets = {
    "Bitcoin": "X:BTCUSD",
    "S&P 500 (SPY ETF)": "X:SPY",
    "Nasdaq 100": "X:QQQ",
    "Or": "X:GCUSD",
    "Ethereum": "X:ETHUSD"
}

# ---------- TITRE ----------
st.title("📊 Tableau de bord Tendance & Valorisation")

# ---------- BOUTONS ----------
col1, col2 = st.columns(2)
with col1:
    force_update = st.button("🔄 Forcer la mise à jour des données")
with col2:
    refresh = st.button("♻️ Actualiser les données")

if force_update:
    st.cache_data.clear()

# ---------- AFFICHAGE MODE ----------
mode = st.radio("Affichage :", ["Tableau (PC)", "Cartes (Mobile)"])

# ---------- TRAITEMENT DES DONNÉES ----------
results = []
dates = {}

for name, ticker in assets.items():
    df = get_polygon_data(ticker)

    if df is not None:
        if not df.empty:
            close, trend, cross, perf, action, last_date = analyze_data(df)
            results.append({
                "Actif": name,
                "Prix actuel": f"{close:,.2f}",
                "Tendance": trend,
                "Croisement MA50/MA200": cross,
                "Évolution 1 mois": f"{perf:.2f} %",
                "Action suggérée": action
            })
            dates[name] = last_date
        else:
            results.append({
                "Actif": name,
                "Prix actuel": "Erreur",
                "Tendance": "Erreur",
                "Croisement MA50/MA200": "Erreur",
                "Évolution 1 mois": "Erreur",
                "Action suggérée": "Erreur"
            })
            dates[name] = "Données vides"
    else:
        results.append({
            "Actif": name,
            "Prix actuel": "Erreur",
            "Tendance": "Erreur",
            "Croisement MA50/MA200": "Erreur",
            "Évolution 1 mois": "Erreur",
            "Action suggérée": "Erreur"
        })
        dates[name] = "Erreur de récupération"

df_result = pd.DataFrame(results)

# ---------- AFFICHAGE ----------
st.subheader("📋 Données actuelles")

if mode == "Tableau (PC)":
    st.dataframe(df_result, use_container_width=True)
else:
    for i, row in df_result.iterrows():
        st.markdown(
            f"""
            ### {row['Actif']}
            **Prix actuel** : {row['Prix actuel']}  
            **Tendance** : {row['Tendance']}  
            **Croisement** : {row['Croisement MA50/MA200']}  
            **Évolution 1 mois** : {row['Évolution 1 mois']}  
            **Action suggérée** : {row['Action suggérée']}
            ---
            """
        )

# ---------- DATES DES DONNÉES ----------
st.markdown("🕒 **Données les plus récentes par actif :**")
for asset, date in dates.items():
    st.write(f"- {asset} : {date}")

# ---------- FOOTER ----------
st.markdown("---")
st.markdown("Développé par redleader1967 🚀")
