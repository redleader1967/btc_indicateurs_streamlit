import streamlit as st
import pandas as pd
from polygon import RESTClient
import datetime

# 🎯 CONFIGURATION
st.set_page_config(page_title="Tendance & Valorisation", page_icon="📊", layout="wide")
st.title("📊 Tableau de bord Tendance & Valorisation")

# 🔑 API Key
API_KEY = st.secrets["polygon_api_key"]

# 🕒 Dates
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365)

# 🔎 Tickers
tickers = {
    "Bitcoin": "X:BTCUSD",
    "S&P 500 (SPY ETF)": "SPY",
    "Nasdaq 100": "QQQ",
    "Or": "X:GCUSD",
    "Ethereum": "X:ETHUSD"
}

# 🎯 FONCTION DATA
@st.cache_data(ttl=3600)
def get_polygon_data(ticker):
    client = RESTClient(API_KEY)
    aggs = client.get_aggs(ticker, 1, "day", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df = pd.DataFrame([a.__dict__ for a in aggs])
    if df.empty:
        return None
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    return df

# 🔁 Rafraîchissement manuel
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()

# 📊 Données
rows = []

for name, ticker in tickers.items():
    df = get_polygon_data(ticker)
    if df is None or len(df) < 50:
        continue

    price = df['close'].iloc[-1]
    ma50 = df['close'].rolling(50).mean().iloc[-1]
    ma200 = df['close'].rolling(200).mean().iloc[-1]
    tendance = "Haussière" if price > ma200 else "Baissière"
    croisement = "Golden Cross ✅" if ma50 > ma200 else "Death Cross ❌"
    pct_change = ((price / df['close'].iloc[-21]) - 1) * 100 if len(df) > 21 else 0

    action = "Renforcer" if tendance == "Haussière" and ma50 > ma200 else "Attendre"

    rows.append({
        "Actif": name,
        "Prix actuel": f"{price:,.2f}",
        "Tendance": tendance + (" ✅" if tendance == "Haussière" else " ❌"),
        "Croisement MA50/MA200": croisement,
        "Évolution 1 mois": f"{pct_change:+.2f} %",
        "Action suggérée": action
    })

# 📋 DataFrame
df_result = pd.DataFrame(rows)

# ✅ AFFICHAGE
mode = st.radio("Affichage :", ["Tableau (PC)", "Cartes (Mobile)"])

if df_result.empty:
    st.error("Aucune donnée disponible.")
else:
    if mode == "Tableau (PC)":
        st.dataframe(df_result, use_container_width=True)
    else:
        for _, row in df_result.iterrows():
            with st.container():
                st.markdown(f"**{row['Actif']}**")
                st.write(f"Prix actuel : {row['Prix actuel']}")
                st.write(f"Tendance : {row['Tendance']}")
                st.write(f"Croisement MA50/MA200 : {row['Croisement MA50/MA200']}")
                st.write(f"Évolution 1 mois : {row['Évolution 1 mois']}")
                st.write(f"Action suggérée : {row['Action suggérée']}")
                st.markdown("---")

# 🔗 PARTAGE
st.markdown("---")
st.markdown("🔗 **Partager cette app :** [Copier le lien](https://rrf7vw6hqpsey3wjl.streamlit.app/)")

# 👨‍💻 Signature
st.markdown("<p style='text-align: center;'>Développé par redleader1967 🚀</p>", unsafe_allow_html=True)
