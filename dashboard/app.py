import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="Super Dashboard ETF", layout="wide")
st.title("🚀 Dashboard Financier Complet")

# Connexion BDD
@st.cache_resource
def get_connection():
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    return create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}")

try:
    engine = get_connection()
    
    # On récupère toutes les données d'un coup
    query = 'SELECT * FROM etf_prices ORDER BY "Date" ASC'
    df_all = pd.read_sql(query, engine)
    liste_etf = df_all['Symbol'].unique().tolist()

    # --- CRÉATION DES ONGLETS ---
    tab1, tab2 = st.tabs(["📊 Comparateur de Performance", "📈 Analyse Technique (Moyennes Mobiles)"])

    # === ONGLET 1 : LE COMPARATEUR (Ton ancienne version) ===
    with tab1:
        st.header("Qui est le plus rentable ?")
        choix_etfs = st.multiselect("Sélectionnez les ETF :", liste_etf, default=liste_etf)
        
        df_filtered = df_all[df_all['Symbol'].isin(choix_etfs)]
        
        if not df_filtered.empty:
            # Graphique simple comparatif
            fig1 = px.line(df_filtered, x='Date', y='Close', color='Symbol', title="Comparaison des prix")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Petit tableau de perf
            st.write("Derniers prix enregistrés :")
            st.dataframe(df_filtered.groupby('Symbol')['Close'].last(), use_container_width=True)

    # === ONGLET 2 : L'ANALYSE TECHNIQUE (Ta nouvelle version Airflow) ===
    with tab2:
        st.header("Stratégie Golden Cross")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            etf_target = st.selectbox("Quel ETF analyser ?", liste_etf)
            st.info("La courbe Jaune (50j) doit croiser la Rouge (200j) vers le haut pour un signal d'achat.")
        
        with col2:
            # On filtre pour un seul ETF
            df_tech = df_all[df_all['Symbol'] == etf_target]
            
            fig2 = go.Figure()
            # Prix
            fig2.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['Close'], mode='lines', name='Prix', line=dict(color='white', width=1)))
            # MA 50
            fig2.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MA_50'], mode='lines', name='Moyenne 50j', line=dict(color='yellow', width=1)))
            # MA 200
            fig2.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MA_200'], mode='lines', name='Moyenne 200j', line=dict(color='red', width=2)))
            
            fig2.update_layout(template="plotly_dark", height=600)
            st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Erreur ou Base de données vide : {e}")