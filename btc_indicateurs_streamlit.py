import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta

#########################################
# CONFIGURATION DE LA PAGE
#########################################

st.set_page_config(
    page_title="Tableau de bord Tendance & Valorisation",
    page_icon="📊",
    layout="centered"
)

#########################################
# LISTE DES ACTIFS
#########################################

assets_yfinance = {
    "S&P 500 (SPY ETF)": "SPY",
    "Nasdaq 100 (QQQ)": "QQQ",
    "Or (Gold)": "GLD"
}

assets_crypto = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum"
}

#########################################
# FONCTIONS
#########################################

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
    # Utilise la dernière valeur non nulle
    series = df[price_col].dropna()
    if series.empty:
        return "Donnée manquante", "Erreur", "Erreur", "Erreur", "Erreur"

    close_price = series.iloc[-1]
    ma50 = series.rolling(window=50).mean().dropna()
    ma200 = series.rolling(window=200).mean().dropna()

    ma50_last = ma50.iloc[-1] if not ma50.empty else np.nan
    ma200_last = ma200.iloc[-1] if not ma200.empty else np.nan

    trend = "Haussière ✅" if close_price > ma200_last else "Baissière ❌"
    cross = "Golden Cross ✅" if ma50_last > ma200_last else "Death Cross ❌"

    if len(series) > 21:
        perf = (close_price / series.iloc[-22] - 1) * 100
        perf = f"{perf:.2f} %"
    else:
        perf = "Insuffisant"

    action = "Renforcer 🟢" if trend.startswith("Haussière") and not perf.startswith("Insuffisant") and float(perf.strip('%')) > 5 else "Attendre ⚪"

    return close_price, trend, cross, perf, action

#########################################
# TITRE ET BOUTONS
#########################################

st.title("📊 Tableau de bord Tendance & Valorisation")

col1, col2 = st.columns(2)
with col1:
    force_update = st.button("🔄 Forcer la mise à jour des données")
with col2:
    refresh = st.button("♻️ Actualiser les données")

if force_update:
    st.cache_data.clear()

mode = st.radio("Affichage :", ["Tableau (PC)", "Cartes (Mobile)"])

#########################################
# ANALYSE DES DONNÉES
#########################################

results = {}

# 📈 YFinance assets
for name, ticker in assets_yfinance.items():
    df = get_yfinance_data(ticker)
    if df is not None and not df.empty:
        close, trend, cross, perf, action = analyze_data(df)
        last_date = df.index[-1].strftime("%Y-%m-%d")
    else:
        close, trend, cross, perf, action = "Erreur", "Erreur", "Erreur", "Erreur", "Erreur"
        last_date = "Non disponible"

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
        close, trend, cross, perf, action = "Erreur", "Erreur", "Erreur", "Erreur", "Erreur"
        last_date = "Non disponible"

    results[name] = {
        "Prix actuel": close,
        "Tendance": trend,
        "Croisement": cross,
        "Évolution 1 mois": perf,
        "Action": action,
        "Dernière date": last_date
    }

#########################################
# AFFICHAGE
#########################################

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

#########################################
# 📘 Explications des prévisions
#########################################

with st.expander("🔎 Comment sont calculées les prévisions ?"):
    st.markdown("""
    ## 🧠 Méthodologie des prévisions

    Cette application évalue la tendance de chaque actif et propose une action (**Renforcer** ou **Attendre**) basée sur des indicateurs techniques classiques :

    ### 📊 Indicateurs utilisés

    #### 1️⃣ Tendance
    - **Haussière ✅** : Le prix actuel est supérieur à sa moyenne mobile 200 jours (**MA200**).
    - **Baissière ❌** : Le prix est en dessous de sa MA200.

    #### 2️⃣ Croisement des moyennes mobiles (MA50/MA200)
    - **Golden Cross ✅** : La moyenne mobile 50 jours (**MA50**) est supérieure à la MA200 ➔ Signal haussier.
    - **Death Cross ❌** : La MA50 est inférieure à la MA200 ➔ Signal baissier.

    #### 3️⃣ Performance mensuelle (sur 1 mois)
    - Variation du prix sur les 30 derniers jours.
    - Si la performance est supérieure à **+5%**, c’est un signal haussier.

    ### 📝 Règles de décision

    - **Renforcer 🟢** : Si la tendance est haussière **et** la performance mensuelle est > 5%.
    - **Attendre ⚪** : Dans tous les autres cas.

    ### 🔎 Sources des données

    - **Actifs traditionnels** : Yahoo Finance (via yfinance).
    - **Cryptomonnaies** : CoinGecko.

    ### ⚠ Avertissement

    Ces signaux sont basés sur des indicateurs techniques. Ils ne remplacent **pas** une analyse fondamentale complète.  
    L’investissement comporte des risques.

    ---
    **Développé par redleader1967 🚀**
    """)
