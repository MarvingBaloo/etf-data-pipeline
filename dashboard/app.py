import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Investisseur Pro & Malin", layout="wide", page_icon="🚀")
st.title("🚀 Station de Trading Complète")

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

# --- FONCTION CALCUL RSI ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

try:
    engine = get_connection()
    
    # Récupération de TOUTES les données (Optimisation)
    # On charge tout d'un coup pour éviter de faire trop de requêtes
    df_all = pd.read_sql('SELECT * FROM etf_prices ORDER BY "Date" ASC', engine)
    liste_etf = df_all['Symbol'].unique().tolist()

    # --- BARRE LATÉRALE (Dates Communes) ---
    st.sidebar.header("📅 Période d'analyse")
    today = datetime.date.today()
    start_default = today - datetime.timedelta(days=365*2)
    date_debut = st.sidebar.date_input("Date de début", start_default)
    date_fin = st.sidebar.date_input("Date de fin", today)

    # Filtrage global par date
    # On convertit les dates pour être sûr que ça matche
    df_all['Date'] = pd.to_datetime(df_all['Date']).dt.date
    df_main = df_all[(df_all['Date'] >= date_debut) & (df_all['Date'] <= date_fin)]

    # --- CRÉATION DES ONGLETS ---
    tab1, tab2 = st.tabs(["🎓 L'Assistant (Débutant)", "📊 Le Comparateur (Pro)"])

    # =========================================================
    # ONGLET 1 : L'ASSISTANT ÉDUCATIF (Ta demande précédente)
    # =========================================================
    with tab1:
        st.header("Analyse détaillée et Verdict")
        
        col_select, col_vide = st.columns([1, 3])
        with col_select:
            etf_target = st.selectbox("Quel actif analyser ?", liste_etf)
        
        # On filtre pour cet ETF spécifique
        df = df_main[df_main['Symbol'] == etf_target].copy()

        if not df.empty:
            # Calculs
            df['RSI'] = calculate_rsi(df['Close'])
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()

            last_row = df.iloc[-1]
            last_price = last_row['Close']
            last_rsi = last_row['RSI']
            last_sma50 = last_row['SMA_50']
            last_sma200 = last_row['SMA_200']

            # Logique Verdict
            signal_type = "wait"
            titre_verdict = "😐 RIEN À SIGNALER"
            message_verdict = "Le marché est calme. Ni vraiment bon marché, ni trop cher."
            
            if last_rsi < 35 and last_sma50 > last_sma200:
                signal_type = "buy"
                titre_verdict = "🟢 BON MOMENT POUR ACHETER ?"
                message_verdict = "Opportunité : Tendance haussière + Prix temporairement bas (Soldes)."
            elif last_rsi > 75:
                signal_type = "sell"
                titre_verdict = "🔴 ATTENTION : RISQUE DE CHUTE"
                message_verdict = "Surchauffe du marché. Le prix est monté trop vite."
            elif last_sma50 > last_sma200:
                signal_type = "buy"
                titre_verdict = "✅ TENDANCE SAINE"
                message_verdict = "Tendance haussière confirmée. Gardez vos positions."

            # Affichage Verdict
            st.markdown(f"""<div class="verdict-box {signal_type}"><h2>{titre_verdict}</h2><p>{message_verdict}</p></div>""", unsafe_allow_html=True)

            # KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric("Prix", f"{last_price:.2f} $")
            c1.metric("Thermomètre (RSI)", f"{last_rsi:.1f}", delta="Trop chaud" if last_rsi > 70 else "Froid" if last_rsi < 30 else "Normal", delta_color="inverse")
            c3.metric("Moyenne 200j", f"{last_sma200:.2f} $", help="La moyenne des prix sur 1 an environ.")

            # Graphique Assistant
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Prix'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], line=dict(color='orange'), name='Moyenne 50j'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_200'], line=dict(color='blue'), name='Moyenne 200j'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], line=dict(color='purple'), name='RSI'), row=2, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📚 Glossaire"):
                st.markdown("RSI < 30 = Pas cher (Achat). RSI > 70 = Trop cher (Vente).")

    # =========================================================
    # ONGLET 2 : LE COMPARATEUR (Le retour !)
    # =========================================================
    with tab2:
        st.header("📊 Comparateur de Performance")
        st.write("Cochez plusieurs cases pour superposer les courbes.")
        
        choix_multiples = st.multiselect("Sélectionnez les ETF à comparer :", liste_etf, default=liste_etf)
        
        # On filtre les données globales
        df_comp = df_main[df_main['Symbol'].isin(choix_multiples)]
        
        if not df_comp.empty:
            # Graphique Comparatif
            # Astuce : On utilise plotly.express qui gère super bien les couleurs auto
            fig_comp = px.line(
                df_comp, 
                x='Date', 
                y='Close', 
                color='Symbol', 
                title="Comparaison des Prix ($)",
                template="plotly_dark"
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tableau récapitulatif
            st.subheader("Performance sur la période sélectionnée")
            summary = []
            for t in choix_multiples:
                d = df_comp[df_comp['Symbol'] == t]
                if not d.empty:
                    p_start = d['Close'].iloc[0]
                    p_end = d['Close'].iloc[-1]
                    perf = ((p_end - p_start) / p_start) * 100
                    summary.append({"ETF": t, "Prix Début": p_start, "Prix Fin": p_end, "Performance": f"{perf:+.2f} %"})
            
            st.dataframe(pd.DataFrame(summary))
            
        else:
            st.warning("Veuillez sélectionner au moins un ETF.")

except Exception as e:
    st.error(f"Erreur technique : {e}")