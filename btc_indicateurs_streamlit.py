import pandas as pd
import requests
import warnings
import streamlit as st

warnings.filterwarnings("ignore")

# ====== CONFIGURATION ======
API_KEY = "JQr2NKnwqbdeXfmWCe58mva2BC8pKIf0"

assets = {
    'Bitcoin': 'X:BTCUSD',
    'S&P 500 (SPY ETF)': 'SPY',
    'Nasdaq 100': 'I:NDX',
    'Or': 'XAUUSD',
    'Ethereum': 'X:ETHUSD'
}

def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return int(data['data'][0]['value'])
    except:
        pass
    return "Indisponible"

@st.cache_data(ttl=3600)
def get_polygon_data(ticker):
    if ticker == 'XAUUSD':
        return get_gold_price()
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2023-04-01/2025-05-01?adjusted=true&sort=asc&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            df['t'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('t', inplace=True)
            df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close'}, inplace=True)
            return df
    return pd.DataFrame()

def get_gold_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=tether-gold&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        price = response.json()['tether-gold']['usd']
        df = pd.DataFrame({'Close': [price]*300})
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=300)
        return df
    return pd.DataFrame()

st.title("📊 Tableau de bord Tendance & Valorisation")

fear_and_greed = get_fear_and_greed()

results = []
haussiers = 0

for name, ticker in assets.items():
    df = get_polygon_data(ticker)

    if df.empty:
        st.warning(f"Aucune donnée pour {name} ({ticker}) ➔ ignoré.")
        continue

    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    close_now = df['Close'].iloc[-1]
    ma200_now = df['MA200'].iloc[-1]
    ma50_now = df['MA50'].iloc[-1]
    date_now = df.index[-1].strftime("%Y-%m-%d")

    df_1mo = df[df.index <= (df.index[-1] - pd.Timedelta(days=30))]
    close_month = df_1mo['Close'].iloc[-1] if not df_1mo.empty else None

    tendance_bool = close_now > ma200_now if pd.notna(ma200_now) else False
    trend = 'Haussière ✅' if tendance_bool else 'Baissière ❌'
    if tendance_bool:
        haussiers += 1

    cross = 'Golden Cross ✅' if ma50_now > ma200_now else 'Death Cross ❌'

    if close_month:
        evolution_pct = round((close_now - close_month) / close_month * 100, 2)
        change = f"+{evolution_pct}% 📈" if evolution_pct > 0 else f"{evolution_pct}% 📉"
    else:
        change = "Pas de données"

    recommandation = "Renforcer 🟢" if tendance_bool and close_month and evolution_pct > 0 else "Attendre ⚪"

    if name == 'Bitcoin' and isinstance(fear_and_greed, int):
        if fear_and_greed > 75:
            recommandation = "Marché trop euphorique ⚠️"

    results.append({
        'Actif': name,
        'Prix actuel': round(close_now, 2),
        'Tendance': trend,
        'Croisement MA50/MA200': cross,
        'Évolution 1 mois': change,
        'Action suggérée': recommandation,
        'Date des données': date_now
    })

df_results = pd.DataFrame(results)

# ===== Affichage =====

st.markdown("## 🔍 Affichage")
mode = st.radio("Choisis ton mode d'affichage :", ["Tableau classique (PC)", "Cartes (Mobile)"])

if mode == "Tableau classique (PC)":
    st.dataframe(df_results, use_container_width=True)
else:
    for index, row in df_results.iterrows():
        st.markdown("---")
        st.markdown(f"### {row['Actif']}")
        st.markdown(f"**Prix actuel** : {row['Prix actuel']}")
        st.markdown(f"**Tendance** : {row['Tendance']}")
        st.markdown(f"**Croisement** : {row['Croisement MA50/MA200']}")
        st.markdown(f"**Évolution 1 mois** : {row['Évolution 1 mois']}")
        st.markdown(f"**Action suggérée** : {row['Action suggérée']}")
        st.markdown(f"*Date des données* : {row['Date des données']}")

# ===== Résumé =====

st.markdown(f"**Fear & Greed Index (Bitcoin)** : {fear_and_greed}/100")
st.markdown(f"**Actifs en tendance haussière** : {haussiers} sur {len(assets)}")

if haussiers >= len(assets) / 2:
    st.success("✅ Marché globalement favorable.")
else:
    st.error("❌ Marché prudent ou défavorable.")

st.caption("* Golden Cross : MA50 > MA200 (signal haussier)")
st.caption("* Death Cross : MA50 < MA200 (signal baissier)")
st.caption("Développé par redleader1967 👑")
