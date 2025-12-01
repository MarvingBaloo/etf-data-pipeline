from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURATION DU DAG ---
default_args = {
    'owner': 'marving',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Définition du DAG : Il se lancera tous les jours à 18h00 (après la fermeture des marchés US)
with DAG(
    dag_id='etf_pipeline_v2_avec_indicateurs',
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    schedule_interval='0 18 * * *', # Notation Cron : 18h00 chaque jour
    catchup=False # On ne veut pas relancer tous les jours manqués depuis 2023
) as dag:

    def etl_process():
        print("--- DÉBUT DE L'ETL AVEC INDICATEURS ---")
        
        # 1. Connexion via le coffre-fort Airflow
        # On récupère les infos qu'on a rentrées dans l'interface Web
        connection = BaseHook.get_connection("postgres_etf")
        # On reconstruit l'URL SQLAlchemy
        db_url = f"postgresql://{connection.login}:{connection.password}@{connection.host}:{connection.port}/{connection.schema}"
        engine = create_engine(db_url)

        etfs = ["SPY", "QQQ", "IWM"]
        
        for ticker in etfs:
            print(f"Traitement de {ticker}...")
            
            # 2. Extraction (On prend 2 ans pour avoir assez d'historique pour la MA200)
            df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True)
            
            # Nettoyage colonnes
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if not df.empty:
                # 3. TRANSFORMATION (Calcul des Moyennes Mobiles)
                # C'est ici que la magie opère !
                df['MA_50'] = df['Close'].rolling(window=50).mean()
                df['MA_200'] = df['Close'].rolling(window=200).mean()
                df['Symbol'] = ticker
                
                # Petit nettoyage : on enlève les lignes vides (le début du calcul des moyennes est vide)
                df = df.dropna()

                # 4. Chargement
                # On utilise 'replace' pour ce ticker. 
                # Note : En prod avancée, on ferait de l'upsert, mais ici 'replace' garantit que les calculs sont à jour.
                # Astuce : On ne veut pas écraser la table à chaque tour de boucle, donc il faudrait gérer ça mieux,
                # mais pour simplifier ici, on va insérer dans une table temporaire ou tout mettre dans une liste et insérer d'un coup.
                # OPTION SIMPLE : On insert tout.
                
                print(f"Insertion de {len(df)} lignes pour {ticker}...")
                # Pour éviter d'écraser les autres, on fait 'append'.
                # Mais avant le premier tour, idéalement il faudrait vider la table.
                # On va faire simple : On append tout, et on aura des doublons qu'on gère plus tard ? 
                # NON, faisons propre.
                pass 

        # --- CORRECTION STRATÉGIE ---
        # Pour faire propre, on télécharge TOUT d'abord, on concatène, et on remplace la table UNE FOIS.
        
        all_data = []
        for ticker in etfs:
            df = yf.download(ticker, period="5y", interval="1d", auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Calculs
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            df['MA_200'] = df['Close'].rolling(window=200).mean()
            df['Symbol'] = ticker
            df = df.dropna()
            
            all_data.append(df)
            print(f"{ticker} traité.")

        # On fusionne les 3 DataFrames en un seul gros
        final_df = pd.concat(all_data)
        
        # On écrase l'ancienne table avec la nouvelle version enrichie
        final_df.to_sql('etf_prices', engine, if_exists='replace')
        print("Base de données mise à jour avec succès (etf_prices).")

    # Définition de la tâche Airflow
    task_etl = PythonOperator(
        task_id='extract_transform_load_etf',
        python_callable=etl_process
    )

    task_etl