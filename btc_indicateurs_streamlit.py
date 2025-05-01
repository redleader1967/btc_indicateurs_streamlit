import streamlit as st
import pandas as pd
from polygon import RESTClient
from datetime import datetime, timedelta

# ----------- CONFIG ----------- #
st.set_page_config(
    page_title="Tableau de bord Tendance & Valorisation",
    page_icon="📊",
    layout="wide"
)

# API Key
API_KEY = st.secrets["polygon_api_key"]
client = RESTClient(API_KEY)

# Tickers à surveiller
assets = {
    "Bitcoin": "X:BTCUSD",
    "S&P 500 (SPY ETF)": "SPY",
    "Nasdaq 100": "QQQ",
    "Or": "XAU/USD",
    "Ethereum": "X:ETHUSD"
}

# ----------- FONCTIONS ----------- #
@st.cache_data(ttl=3600)
def get_polygon_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    try:
        aggs = client.get_aggs(ticker, 1, "day", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        df = pd.DataFrame(aggs)
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('date')
        return df
    except Exception as e:
        return pd.DataFrame(), str(e)

def analyze_data(df):
    if df.empty:
        return "Erreur", "Erreur", "None", "None", "None"
    close = df['close'].iloc[-1]
    ma50 = df['close'].rolling(window=50).mean().iloc[-1]
    ma200 = df['close'].rolling(window=200).mean().iloc[-1]
    trend = "Haussière ✅" if close > ma200 else "Baissière ❌"
    cross = "Golden Cross ✅" if ma50 > ma200 else "Death Cross ❌"
    perf = ((close - df['close'].iloc[-22]) / df['close'].iloc[-22]) * 100 if len(df) > 22 else "N/A"
    action = "Renforcer 🟢" if trend == "Haussière ✅" else "Attendre ⚪️"
    return round(close, 2), trend, cross, f"{perf:.2f} %" if perf != "N/A" else "N/A", action

# ----------- UI ----------- #
st.title("📊 Tableau de bord Tendance & Valorisation")

if st.button("🔄 Forcer la mise à jour des données"):
    st.cache_data.clear()

affichage = st.radio("Affichage :", ["Tableau (PC)", "Cartes (Mobile)"])

# ----------- ANALYSE ----------- #
results = []
max_date = datetime(2000,1,1)

for name, ticker in assets.items():
    df, error = get_polygon_data(ticker)
    if not df.empty:
        close, trend, cross, perf, action = analyze_data(df)
        last_date = df['date'].max()
        max_date = max(max_date, last_date)
    else:
        close, trend, cross, perf, action = "Erreur", "Erreur", "None", "None", "None"
        last_date = "Aucune donnée"
    results.append({
        "Actif": name,
        "Prix actuel": close,
        "Tendance": trend,
        "Croisement MA50/MA200": cross,
        "Évolution 1 mois": perf,
        "Action suggérée": action,
        "Dernière date": last_date
    })

df_final = pd.DataFrame(results)

# ----------- AFFICHAGE ----------- #
st.divider()

if affichage == "Tableau (PC)":
    st.dataframe(df_final.drop(columns=["Dernière date"]), use_container_width=True)
else:
    for i, row in df_final.iterrows():
        st.subheader(f"📌 {row['Actif']}")
        st.write(f"**Prix actuel :** {row['Prix actuel']}")
        st.write(f"**Tendance :** {row['Tendance']}")
        st.write(f"**Croisement MA50/MA200 :** {row['Croisement MA50/MA200']}")
        st.write(f"**Évolution 1 mois :** {row['Évolution 1 mois']}")
        st.write(f"**Action suggérée :** {row['Action suggérée']}")
        st.divider()

# ----------- ALERTE DONNÉES TROP VIEILLES ----------- #
if max_date < datetime.now() - timedelta(days=2):
    st.error(f"⚠ Les données sont anciennes (dernière date : {max_date.date()}). Vérifie ton quota Polygon ou patiente.")

else:
    st.success(f"✅ Données mises à jour au : {max_date.date()}")

st.markdown("---")
st.markdown("Développé par **redleader1967 🚀**")
