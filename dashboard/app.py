import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import numpy as np

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Investisseur Pro & Malin", layout="wide", page_icon="🚀")
st.title("🚀 Station de Trading (Version Euro €)")

# --- STYLE CSS ---
st.markdown("""
<style>
    .verdict-box { padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .buy { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
    .sell { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
    .wait { background-color: #fff3cd; color: #856404; border: 2px solid #ffeeba; }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION BDD ---
@st.cache_resource
def get_connection():
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    return create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}")

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

try:
    engine = get_connection()
    df_all = pd.read_sql('SELECT * FROM etf_prices ORDER BY "Date" ASC', engine)
    liste_etf = df_all['Symbol'].unique().tolist()

    # --- BARRE LATÉRALE ---
    st.sidebar.header("📅 Période d'analyse")
    today = datetime.date.today()
    start_default = today - datetime.timedelta(days=365*5)
    date_debut = st.sidebar.date_input("Date de début", start_default)
    date_fin = st.sidebar.date_input("Date de fin", today)

    df_all['Date'] = pd.to_datetime(df_all['Date'])
    df_main = df_all[(df_all['Date'].dt.date >= date_debut) & (df_all['Date'].dt.date <= date_fin)]

    # --- ONGLETS ---
    tab1, tab2 = st.tabs(["🎓 L'Assistant & Performance", "📊 Le Comparateur"])

    # === ONGLET 1 ===
    with tab1:
        col_select, col_vide = st.columns([1, 3])
        with col_select:
            # Si la liste est vide (bug téléchargement), on gère l'erreur
            if liste_etf:
                etf_target = st.selectbox("Quel actif analyser ?", liste_etf)
                df = df_main[df_main['Symbol'] == etf_target].copy()
            else:
                st.error("Aucun ETF trouvé en base. Relancez Airflow.")
                df = pd.DataFrame()

        if not df.empty:
            df['RSI'] = calculate_rsi(df['Close'])
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()

            last_row = df.iloc[-1]
            last_price = last_row['Close']
            last_rsi = last_row['RSI']
            last_sma50 = last_row['SMA_50']
            last_sma200 = last_row['SMA_200']

            # CAGR
            price_start = df['Close'].iloc[0]
            price_end = df['Close'].iloc[-1]
            total_return = (price_end - price_start) / price_start
            days_diff = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
            years_diff = days_diff / 365.25
            cagr = ((price_end / price_start) ** (1 / years_diff)) - 1 if years_diff > 0 else 0

            # Perf Annuelle
            df_yearly = df.set_index('Date').resample('YE')['Close'].last()
            df_yearly_pct = df_yearly.pct_change() * 100
            df_yearly_pct = df_yearly_pct.dropna()

            # Verdict
            signal_type = "wait"
            titre_verdict = "😐 RIEN À SIGNALER"
            message_verdict = "Le marché est calme."
            
            if last_rsi < 35 and last_sma50 > last_sma200:
                signal_type = "buy"
                titre_verdict = "🟢 BON MOMENT POUR ACHETER ?"
                message_verdict = "Opportunité : Tendance haussière + Prix temporairement bas."
            elif last_rsi > 75:
                signal_type = "sell"
                titre_verdict = "🔴 ATTENTION : RISQUE DE CHUTE"
                message_verdict = "Surchauffe du marché."
            elif last_sma50 > last_sma200:
                signal_type = "buy"
                titre_verdict = "✅ TENDANCE SAINE"
                message_verdict = "Tendance haussière confirmée."

            st.markdown(f"""<div class="verdict-box {signal_type}"><h2>{titre_verdict}</h2><p>{message_verdict}</p></div>""", unsafe_allow_html=True)

            # KPIs (CORRIGÉS EN EUROS)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Prix Actuel", f"{last_price:.2f} €") # <--- ICI
            c2.metric("Rendement Annuel Moyen", f"{cagr*100:.2f} %")
            c3.metric("Rendement Total", f"{total_return*100:.2f} %")
            c4.metric("Tendance", "Hausse" if last_sma50 > last_sma200 else "Baisse")

            # Graphique 1
            st.subheader("🔎 Analyse Technique")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Prix'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], line=dict(color='orange'), name='MA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_200'], line=dict(color='blue'), name='MA 200'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], line=dict(color='purple'), name='RSI'), row=2, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # Graphique 2 (Annuel)
            st.subheader("📅 Détail : Performance par Année")
            if not df_yearly_pct.empty:
                colors = ['green' if v >= 0 else 'red' for v in df_yearly_pct.values]
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    x=df_yearly_pct.index.year,
                    y=df_yearly_pct.values,
                    marker_color=colors,
                    text=df_yearly_pct.values,
                    texttemplate='%{text:.1f}%',
                    textposition='outside'
                ))
                fig_bar.update_layout(title=f"Gains et Pertes annuels - {etf_target}", yaxis_title="Pourcentage (%)", template="plotly_dark", height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Période trop courte pour l'histogramme annuel.")

    # === ONGLET 2 ===
    with tab2:
        st.header("📊 Comparateur de Performance")
        choix_multiples = st.multiselect("Sélectionnez les ETF :", liste_etf, default=liste_etf)
        df_comp = df_main[df_main['Symbol'].isin(choix_multiples)]
        
        if not df_comp.empty:
            fig_comp = px.line(df_comp, x='Date', y='Close', color='Symbol', title="Prix comparés (€)", template="plotly_dark")
            st.plotly_chart(fig_comp, use_container_width=True)
            
            st.write("Résumé des performances :")
            summary = []
            for t in choix_multiples:
                d = df_comp[df_comp['Symbol'] == t]
                if not d.empty:
                    p_start = d['Close'].iloc[0]
                    p_end = d['Close'].iloc[-1]
                    total_perf = ((p_end - p_start) / p_start) * 100
                    days = (d['Date'].iloc[-1] - d['Date'].iloc[0]).days
                    years = days / 365.25
                    cagr_perf = (((p_end / p_start) ** (1/years)) - 1) * 100 if years > 0 else 0

                    summary.append({
                        "ETF": t, 
                        "Prix Début": f"{p_start:.2f} €", 
                        "Prix Fin": f"{p_end:.2f} €", 
                        "Total (%)": f"{total_perf:+.2f} %",
                        "Annuel Moyen (%)": f"{cagr_perf:+.2f} %"
                    })
            st.dataframe(pd.DataFrame(summary))

except Exception as e:
    st.error(f"Erreur technique : {e}")