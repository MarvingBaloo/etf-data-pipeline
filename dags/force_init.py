import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

# Configuration manuelle de la connexion (puisqu'on ne passe pas par Airflow)
DB_USER = "user_etf"
DB_PASS = "password_etf"
DB_HOST = "postgres"
DB_NAME = "etf_data"
CONN_STR = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

def force_initialization():
    print("--- DÉMARRAGE FORCÉ ---")
    engine = create_engine(CONN_STR)
    
    # Liste des ETF
    etfs = ["CSPX.AS", "CNDX.AS", "ZPRR.DE", "AGGH.AS"]
    
    all_data = []
    
    for ticker in etfs:
        print(f"Téléchargement de {ticker}...")
        try:
            # On force le téléchargement sans ajustement pour tester
            df = yf.download(ticker, period="2y", interval="1d", progress=False)
            
            # Correction du bug MultiIndex de yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if not df.empty and 'Close' in df.columns:
                df['Symbol'] = ticker
                # On garde les colonnes essentielles
                df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Symbol']]
                all_data.append(df)
                print(f"✅ OK : {len(df)} lignes.")
            else:
                print(f"❌ ERREUR : Pas de données pour {ticker}")
                
        except Exception as e:
            print(f"❌ CRASH sur {ticker}: {e}")

    if all_data:
        print("Fusion des données...")
        final_df = pd.concat(all_data)
        
        print("Création de la table 'etf_prices' dans Postgres...")
        final_df.to_sql('etf_prices', engine, if_exists='replace')
        print("🎉 SUCCÈS : Table créée ! Tu peux lancer le Dashboard.")
    else:
        print("💀 ÉCHEC TOTAL : Aucune donnée récupérée. Vérifie ta connexion internet.")

if __name__ == "__main__":
    force_initialization()