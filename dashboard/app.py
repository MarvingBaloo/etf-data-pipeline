import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Investisseur Pro", layout="wide", page_icon="🦁")
st.title("🦁 Station de Trading & Simulation (V9.1 Correctif)")

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
    
    if df_all.empty:
        st.error("La base de données est vide. Lancez le DAG Airflow.")
        st.stop()

    liste_etf = df_all['Symbol'].unique().tolist()
    df_all['Date'] = pd.to_datetime(df_all['Date'])

    # --- BARRE LATÉRALE (Uniquement pour les dates globales) ---
    st.sidebar.header("📅 Dates de référence")
    # Note : J'ai retiré le sélecteur d'ETF d'ici pour le remettre dans les onglets
    
    # --- ONGLETS ---
    tab1, tab2, tab3 = st.tabs(["🎓 L'Assistant", "📊 Comparateur", "🔮 Simulateur & Bilan"])

    # =========================================================
    # ONGLET 1 : L'ASSISTANT (CORRIGÉ : SÉLECTEUR EST REVENU)
    # =========================================================
    with tab1:
        st.header("Analyse Technique & Verdict")
        
        # --- LE SÉLECTEUR EST DE RETOUR ICI ---
        col_sel_ass, col_vide_ass = st.columns([1, 3])
        with col_sel_ass:
            etf_assistant = st.selectbox("Quel actif analyser ?", liste_etf, key="sel_assistant")

        # Analyse sur 2 ans glissants pour la technique
        date_debut_tech = datetime.date.today() - datetime.timedelta(days=365*2)
        df = df_all[(df_all['Symbol'] == etf_assistant) & (df_all['Date'].dt.date >= date_debut_tech)].copy()

        if not df.empty:
            df['RSI'] = calculate_rsi(df['Close'])
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last_row = df.iloc[-1]
            last_rsi = last_row['RSI']
            last_sma50 = last_row['SMA_50']
            last_sma200 = last_row['SMA_200']

            signal_type, titre_verdict = "wait", "😐 NEUTRE"
            if last_rsi < 35 and last_sma50 > last_sma200:
                signal_type, titre_verdict = "buy", "🟢 OPPORTUNITÉ"
            elif last_rsi > 75:
                signal_type, titre_verdict = "sell", "🔴 SURCHAUFFE"
            elif last_sma50 > last_sma200:
                signal_type, titre_verdict = "buy", "✅ TENDANCE HAUSSIÈRE"

            st.markdown(f"""<div class="verdict-box {signal_type}"><h2>{titre_verdict}</h2></div>""", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Prix Actuel", f"{last_row['Close']:.2f} €")
            c2.metric("RSI", f"{last_rsi:.1f}")
            c3.metric("Tendance", "Hausse" if last_sma50 > last_sma200 else "Baisse")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Prix'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], line=dict(color='orange'), name='MA50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_200'], line=dict(color='blue'), name='MA200'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], line=dict(color='purple'), name='RSI'), row=2, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=2, col=1)
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

    # =========================================================
    # ONGLET 2 : COMPARATEUR (Inchangé)
    # =========================================================
    with tab2:
        st.header("Comparaison Multi-Actifs")
        choix = st.multiselect("Comparer :", liste_etf, default=liste_etf)
        
        # Filtre date spécifique au comparateur
        d_start = st.date_input("Depuis le", datetime.date(2018, 1, 1), key="date_comp")
        
        df_c = df_all[(df_all['Symbol'].isin(choix)) & (df_all['Date'].dt.date >= d_start)]
        if not df_c.empty:
            fig_c = px.line(df_c, x='Date', y='Close', color='Symbol', title="Comparaison Prix (€)", template="plotly_dark")
            st.plotly_chart(fig_c, use_container_width=True)

    # =========================================================
    # ONGLET 3 : SIMULATEUR & BILAN (CORRIGÉ : SÉLECTEUR AJOUTÉ)
    # =========================================================
    with tab3:
        st.header("🔮 Bilan Historique & Simulation")
        
        col_sel_sim, col_vide_sim = st.columns([1, 3])
        with col_sel_sim:
            # Sélecteur spécifique pour le simulateur
            etf_sim = st.selectbox("Actif à simuler", liste_etf, key="sel_sim")
        
        # --- PARTIE 1 : HISTOGRAMME ANNUEL ---
        st.subheader(f"1. Rendements Annuels : {etf_sim}")
        
        col_hist1, col_hist2 = st.columns([1, 3])
        with col_hist1:
            min_year = int(df_all['Date'].dt.year.min())
            max_year = int(df_all['Date'].dt.year.max())
            years_selected = st.slider("Période :", min_value=min_year, max_value=max_year, value=(min_year, max_year))
        
        with col_hist2:
            df_target = df_all[df_all['Symbol'] == etf_sim].copy()
            df_yearly = df_target.set_index('Date').resample('YE')['Close'].last()
            df_yearly_pct = df_yearly.pct_change() * 100
            
            mask_years = (df_yearly_pct.index.year >= years_selected[0]) & (df_yearly_pct.index.year <= years_selected[1])
            df_yearly_pct = df_yearly_pct[mask_years]
            
            if not df_yearly_pct.empty:
                colors = ['#00CC96' if v >= 0 else '#EF553B' for v in df_yearly_pct.values]
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    x=df_yearly_pct.index.year, y=df_yearly_pct.values,
                    marker_color=colors, text=df_yearly_pct.values,
                    texttemplate='%{text:.1f}%', textposition='outside'
                ))
                fig_bar.update_layout(title=f"Performance par an", template="plotly_dark", height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Pas assez de données.")

        st.divider()

        # --- PARTIE 2 : SIMULATEUR DCA ---
        st.subheader(f"2. Simulation DCA sur {etf_sim}")
        
        c_sim1, c_sim2, c_sim3 = st.columns(3)
        with c_sim1: montant = st.number_input("Montant (€)", min_value=10, value=200, step=10)
        with c_sim2: freq = st.selectbox("Fréquence", ["Mensuel", "Annuel"])
        with c_sim3: date_start_sim = st.date_input("Début", datetime.date(2015, 1, 1))

        if st.button("🚀 Simuler"):
            df_sim = df_target[df_target['Date'].dt.date >= date_start_sim].copy()
            
            if not df_sim.empty:
                rule = 'MS' if freq == "Mensuel" else 'YE'
                df_resampled = df_sim.set_index('Date').resample(rule)['Close'].first().dropna()
                
                investi_total = 0
                nb_actions = 0
                historique_portfolio = []
                historique_investi = []
                
                for date, price in df_resampled.items():
                    nb_actions += montant / price
                    investi_total += montant
                    valeur_portfolio = nb_actions * price
                    historique_portfolio.append({'Date': date, 'Valeur': valeur_portfolio})
                    historique_investi.append({'Date': date, 'Valeur': investi_total})
                
                df_res_sim = pd.DataFrame(historique_portfolio)
                df_res_inv = pd.DataFrame(historique_investi)
                
                valeur_finale = df_res_sim.iloc[-1]['Valeur']
                gain_net = valeur_finale - investi_total
                perf_pct = (gain_net / investi_total) * 100
                
                st.success(f"Résultat : {valeur_finale:,.0f} € (Gain: {perf_pct:+.2f}%)")
                
                fig_sim = go.Figure()
                fig_sim.add_trace(go.Scatter(x=df_res_sim['Date'], y=df_res_sim['Valeur'], mode='lines', name='Portefeuille', line=dict(color='#00CC96'), fill='tozeroy'))
                fig_sim.add_trace(go.Scatter(x=df_res_inv['Date'], y=df_res_inv['Valeur'], mode='lines', name='Investi', line=dict(color='white', dash='dash')))
                fig_sim.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_sim, use_container_width=True)

except Exception as e:
    st.error(f"Erreur : {e}")