import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
import os
import time

def extract_and_load_data():
    print("--- DÉBUT DU PROCESSUS ETL MULTI-ETF ---")
    
    # 1. Connexion BDD
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
    engine = create_engine(connection_string)

    # 2. Définition de la liste des ETF à analyser
    # SPY = S&P 500 (Général)
    # QQQ = Nasdaq (Tech / Croissance)
    # IWM = Russell 2000 (Small Caps / Potentiel élevé)
    etf_list = ["SPY", "QQQ", "IWM"]
    
    # 3. Nettoyage initial (Optionnel mais propre)
    # On vide la table avant de commencer pour éviter les doublons lors de nos tests
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS etf_prices"))
        conn.commit() # Très important pour valider la suppression
        print("Ancienne table supprimée (si elle existait).")

    # 4. La Boucle : On traite chaque ETF un par un
    for ticker in etf_list:
        print(f"\nTraitement de : {ticker}...")
        
        # On télécharge le MAX d'historique disponible
        data = yf.download(ticker, period="max", interval="1d", auto_adjust=True)
        
        # Nettoyage des colonnes (comme avant)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        if not data.empty:
            # --- ÉTAPE CRUCIALE ---
            # On ajoute une colonne pour dire "Ces lignes appartiennent à SPY"
            data['Symbol'] = ticker
            
            # On insère dans la base
            # if_exists='append' : on ajoute à la suite des autres
            data.to_sql('etf_prices', engine, if_exists='append')
            
            print(f"Succès : {len(data)} lignes insérées pour {ticker}")
        else:
            print(f"Attention : Aucune donnée pour {ticker}")
            
    print("\n--- FIN DU PROCESSUS ---")

if __name__ == "__main__":
    time.sleep(5)
    extract_and_load_data()