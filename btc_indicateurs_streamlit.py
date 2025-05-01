import yfinance as yf
import pandas as pd
import warnings
import requests
import streamlit as st

warnings.filterwarnings("ignore")

# Fonction pour récupérer le Fear & Greed Index
def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return int(data['data'][0]['value'])
        else:
            return "Indisponible"
    except:
        return "Erreur"

# Liste des actifs
assets = {
    'Bitcoin': 'BTC-USD',
    'S&P 500': '^GSPC',
    'Nasdaq 100': '^NDX',
    'Or': 'GC=F',
    'US 10Y': '^TNX',
    'Ethereum': 'ETH-USD'
}

# === Interface Streamlit ===
st.title("📊 Tableau de bord Tendance & Valorisation")

fear_and_greed = get_fear_and_greed()

results = []
haussiers = 0

for name, ticker in assets.items():
    df = yf.download(ticker, period='13mo', interval='1d', progress=False)
    df.dropna(inplace=True)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    close_now = df['Close'].iloc[-1]
    ma200_now = df['MA200'].iloc[-1]
    ma50_now = df['MA50'].iloc[-1]

    # Prix il y a 1 mois
    try:
        df_1mo = df[df.index <= (df.index[-1] - pd.Timedelta(days=30))]
        close_month = df_1mo['Close'].iloc[-1]
    except:
        close_month = None

    if pd.notna(ma200_now):
        tendance_bool = close_now > ma200_now
        trend = 'Haussière ✅' if tendance_bool else 'Baissière ❌'
        if tendance_bool:
            haussiers += 1
    else:
        trend = 'Pas assez de données'
        tendance_bool = False

    if pd.notna(ma50_now) and pd.notna(ma200_now):
        cross = 'Golden Cross ✅' if ma50_now > ma200_now else 'Death Cross ❌'
    else:
        cross = 'N/A'

    if close_month:
        evolution_pct = round((close_now - close_month) / close_month * 100, 2)
        hausse_bool = evolution_pct > 0
        change = f"+ {evolution_pct} % 📈" if hausse_bool else f"{evolution_pct} % 📉"
    else:
        change = "Pas de données"

    if tendance_bool and hausse_bool:
        recommandation = "Renforcer 🟢"
    else:
        recommandation = "Attendre ⚪"

    if name == 'Bitcoin' and isinstance(fear_and_greed, int):
        if fear_and_greed > 75:
            recommandation = "Marché trop euphorique ⚠️"

    results.append({
        'Actif': name,
        'Ticker': ticker,
        'Prix actuel': round(close_now, 2),
        'MA200': round(ma200_now, 2) if pd.notna(ma200_now) else 'N/A',
        'Tendance': trend,
        'Croisement MA50/MA200': cross,
        'Évolution 1 mois': change,
        'Action suggérée': recommandation
    })

df_results = pd.DataFrame(results)

st.dataframe(df_results)

st.markdown(f"**Fear & Greed Index (Bitcoin)** : {fear_and_greed}/100")

total_actifs = len(assets)
st.markdown(f"**Actifs en tendance haussière** : {haussiers} sur {total_actifs}")

if haussiers >= total_actifs / 2:
    st.success("✅ Marché globalement favorable.")
else:
    st.error("❌ Marché prudent ou défavorable.")

st.caption("* Golden Cross : MA50 > MA200 (signal haussier)")
st.caption("* Death Cross : MA50 < MA200 (signal baissier)")
