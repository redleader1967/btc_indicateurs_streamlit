import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta

# ---------- CONFIGURATION ----------
st.set_page_config(
    page_title="Tableau de bord Tendance & Valorisation",
    page_icon="📊",
    layout="centered"
)

# ---------- LISTE DES ACTIFS ----------
assets_yfinance = {
    "S&P 500 (SPY ETF)": "SPY",
    "Nasdaq 100 (QQQ)": "QQQ",
    "Or (Gold)": "GLD"
}

assets_crypto = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum"
}

# ---------- FONCTIONS ----------

@st.cache_data(ttl=3600)
def get_yfinance_data(ticker):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=90)
    df = yf.download(ticker, start=start_date, end=end_date)
    if not df.empty:
        return df
    else:
        return None

@st.cache_data(ttl=3600)
def get_crypto_price(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    params = {"vs_currency": "usd", "days": "90"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        prices = response.json()["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("date")
        df = df.resample('1D').last().dropna()
        return df
    else:
        return None

def analyze_data(df, price_col="Close"):
    if price_col == "Close":
        close_price = df[price_col].iloc[-1]
        series = df[price_col]
    else:
        close_price = df[price_col].iloc[-1]
        series = df[price_col]

    ma50 = series.rolling(window=50).mean().iloc[-1]
    ma200 = series.rolling(window=200).mean().iloc[-1] if len(series) >= 200 else np.nan

    trend = "Haussière ✅" if close_price > ma200 else "Baissière ❌"
    cross = "Golden Cross ✅" if ma50 > ma200 else "Death Cross ❌"

    if len(series) > 21:
        perf = (close_price / series.iloc[-22] - 1) * 100
    else:
        perf = np.nan

    action = "Renforcer 🟢" if trend.startswith("Haussière") else "Attendre ⚪️"

    return close_price, trend, cross, f"{perf:.2f} %", action

# ---------- TITRE ----------
st.title("📊 Tableau de bord Tendance & Valorisation")

col1, col2 = st.columns(2)
with col1:
    force_update = st.button("🔄 Forcer la mise à jour des données")
with col2:
    refresh = st.button("♻️ Actualiser les données")

if force_update:
    st.cache_data.clear()

mode = st.radio("Affichage :", ["Tableau (PC)", "Cartes (Mobile)"])

# ---------- ANALYSE ----------
results = {}

# 📈 YFinance assets
for name, ticker in assets_yfinance.items():
    df = get_yfinance_data(ticker)
    if df is not None and not df.empty:
        close, trend, cross, perf, action = analyze_data(df)
        last_date = df.index[-1].strftime("%Y-%m-%d")
    else:
        close, trend, cross, perf, action, last_date = "Erreur", "Erreur", "Erreur", "Erreur", "Erreur", "N/A"

    results[name] = {
        "Prix actuel": close,
        "Tendance": trend,
        "Croisement": cross,
        "Évolution 1 mois": perf,
        "Action": action,
        "Dernière date": last_date
    }

# 📊 Crypto assets
for name, coin in assets_crypto.items():
    df = get_crypto_price(coin)
    if df is not None and not df.empty:
        df = df.rename(columns={"price": "Close"})
        close, trend, cross, perf, action = analyze_data(df, price_col="Close")
        last_date = df.index[-1].strftime("%Y-%m-%d")
    else:
        close, trend, cross, perf, action, last_date = "Erreur", "Erreur", "Erreur", "Erreur", "Erreur", "N/A"

    results[name] = {
        "Prix actuel": close,
        "Tendance": trend,
        "Croisement": cross,
        "Évolution 1 mois": perf,
        "Action": action,
        "Dernière date": last_date
    }

# ---------- AFFICHAGE ----------
df_result = pd.DataFrame.from_dict(results, orient='index')
df_result.reset_index(inplace=True)
df_result.rename(columns={"index": "Actif"}, inplace=True)

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
            **Croisement** : {row['Croisement']}  
            **Évolution 1 mois** : {row['Évolution 1 mois']}  
            **Action** : {row['Action']}  
            **Dernière date** : {row['Dernière date']}
            ---
            """
        )

st.markdown("---")
st.markdown("Développé par **redleader1967 🚀**")
