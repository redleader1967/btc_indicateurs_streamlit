import streamlit as st
import pandas as pd
from polygon import RESTClient
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Tableau de bord Tendance & Valorisation", layout="centered")

# 🔑 Clé API
API_KEY = st.secrets["polygon_api_key"]
client = RESTClient(API_KEY)

# 🎯 Actifs à suivre
tickers = {
    "Bitcoin": "X:BTCUSD",
    "S&P 500 (SPY ETF)": "SPY",
    "Nasdaq 100": "QQQ",
    "Or": "X:GCUSD",
    "Ethereum": "X:ETHUSD"
}

# 📅 Dates
end_date = datetime.now(pytz.UTC)
start_date = end_date - timedelta(days=365 * 1.5)

# 📥 Fonction pour récupérer les données Polygon
@st.cache_data(ttl=3600)
def get_polygon_data(ticker):
    aggs = client.get_aggs(
        ticker,
        1,
        "day",
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    data = [{
        "date": datetime.utcfromtimestamp(a.timestamp / 1000),
        "close": a.close
    } for a in aggs]
    df = pd.DataFrame(data).set_index("date")
    return df

# 📝 Fonction pour calculer la tendance et les indicateurs
def analyze_asset(name, ticker):
    try:
        df = get_polygon_data(ticker)
        if df.empty:
            return {"Actif": name, "Prix actuel": "N/A", "Tendance": "N/A", "Date": "Aucune donnée"}
        ma50 = df["close"].rolling(50).mean()
        ma200 = df["close"].rolling(200).mean()
        last_close = df["close"].iloc[-1]
        last_date = df.index[-1].strftime("%Y-%m-%d")

        tendance = "Haussière ✅" if last_close > ma200.iloc[-1] else "Baissière ❌"
        cross = "Golden Cross ✅" if ma50.iloc[-1] > ma200.iloc[-1] else "Death Cross ❌"

        try:
            change = ((df["close"].iloc[-1] - df["close"].iloc[-21]) / df["close"].iloc[-21]) * 100
        except IndexError:
            change = 0

        action = "Renforcer 🟢" if tendance.startswith("Haussière") else "Attendre ⚪"

        return {
            "Actif": name,
            "Prix actuel": f"{last_close:,.2f}",
            "Tendance": tendance,
            "Croisement MA50/MA200": cross,
            "Évolution 1 mois": f"{change:.2f} %",
            "Action suggérée": action,
            "Date": last_date
        }

    except Exception as e:
        return {"Actif": name, "Prix actuel": "Erreur", "Tendance": "Erreur", "Date": str(e)}

# 🏷️ Interface Streamlit
st.title("📊 Tableau de bord Tendance & Valorisation")

if st.button("🔄 Forcer la mise à jour des données"):
    st.cache_data.clear()

if st.button("🔃 Actualiser les données"):
    pass  # Rafraîchit simplement

# 📊 Analyse
results = []
for name, ticker in tickers.items():
    results.append(analyze_asset(name, ticker))

df_results = pd.DataFrame(results)

# 🖥️ Affichage
if not df_results.empty and df_results["Prix actuel"].ne("N/A").any():
    st.dataframe(df_results, use_container_width=True)
    st.write(f"🕒 Données les plus récentes par actif :")
    for idx, row in df_results.iterrows():
        st.write(f"- **{row['Actif']}** : {row['Date']}")
else:
    st.error("Aucune donnée disponible.")

st.markdown("---")
st.markdown("Développé par redleader1967 🚀")
