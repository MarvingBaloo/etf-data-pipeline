import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.express as px

# 1. Configuration de la page
st.set_page_config(page_title="Comparateur ETF", layout="wide")

st.title("📊 Comparateur de Performance ETF")
st.markdown("Analysez et comparez la rentabilité du **SPY**, **QQQ** et **IWM** sur 30 ans.")

# 2. Connexion Base de Données
@st.cache_resource
def get_database_connection():
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
    return create_engine(connection_string)

try:
    engine = get_database_connection()
    
    # 3. Récupération de TOUTES les données d'un coup
    # C'est plus simple de tout charger et de filtrer avec Pandas ensuite
    query = 'SELECT "Date", "Close", "Symbol" FROM etf_prices ORDER BY "Date" ASC'
    df_all = pd.read_sql(query, engine)
    
    # Liste des symboles disponibles
    liste_etf_dispo = df_all['Symbol'].unique().tolist()

    # --- BARRE LATÉRALE (Filtres) ---
    st.sidebar.header("Configuration")
    
    # Multiselect : L'utilisateur peut en cocher plusieurs
    # default=liste_etf_dispo : Par défaut, ils sont tous sélectionnés
    choix_etfs = st.sidebar.multiselect(
        "Sélectionnez les ETF à comparer :", 
        options=liste_etf_dispo,
        default=liste_etf_dispo
    )
    
    # On filtre les données selon le choix de l'utilisateur
    df_filtered = df_all[df_all['Symbol'].isin(choix_etfs)]

    if not df_filtered.empty:
        # --- GRAPHIQUE COMPARATIF ---
        st.subheader("Évolution comparée des prix ($)")
        
        # L'argument magique ici est color='Symbol'
        # Il crée automatiquement une courbe différente pour chaque ETF
        fig = px.line(
            df_filtered, 
            x='Date', 
            y='Close', 
            color='Symbol', 
            title="Historique des prix comparés",
            template="plotly_dark" # Un look un peu plus moderne
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLEAU DE PERFORMANCE (KPI) ---
        st.subheader("Tableau de bord de rentabilité")
        
        # On va créer un petit tableau récapitulatif
        summary_data = []
        
        for ticker in choix_etfs:
            # On prend les données juste pour ce ticker
            df_ticker = df_filtered[df_filtered['Symbol'] == ticker]
            
            if not df_ticker.empty:
                start_price = df_ticker['Close'].iloc[0]
                end_price = df_ticker['Close'].iloc[-1]
                total_return = ((end_price - start_price) / start_price) * 100
                
                summary_data.append({
                    "ETF": ticker,
                    "Prix Départ ($)": round(start_price, 2),
                    "Prix Fin ($)": round(end_price, 2),
                    "Performance Totale (%)": f"+{total_return:.2f} %"
                })
        
        # Affichage du tableau propre
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        
    else:
        st.warning("Veuillez sélectionner au moins un ETF dans la barre latérale.")

except Exception as e:
    st.error(f"Erreur technique : {e}")