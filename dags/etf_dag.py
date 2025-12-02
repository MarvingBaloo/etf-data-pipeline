from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURATION DU DAG ---
default_args = {
    'owner': 'marving',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='etf_pipeline_v2_avec_indicateurs',
    default_args=default_args,
    start_date=datetime(2005, 1, 1),
    schedule_interval='0 18 * * *', 
    catchup=False
) as dag:

    def etl_process():
        print("--- DÉBUT ETL : VERSION EUROPE (ACC) ---")
        
        # 1. Connexion
        connection = BaseHook.get_connection("postgres_etf")
        db_url = f"postgresql://{connection.login}:{connection.password}@{connection.host}:{connection.port}/{connection.schema}"
        engine = create_engine(db_url)

        # 2. LISTE DES ETF EUROPÉENS (CAPITALISANTS) EN EUROS
        # CSPX.AS = S&P 500 (Euronext Amsterdam)
        # CNDX.AS = Nasdaq 100 (Euronext Amsterdam)
        # R2US.DE = Russell 2000 (Xetra Allemagne - Small Caps)
        etfs = ["CSPX.AS", "CNDX.AS", "ZPRR.DE", "AGGH.AS"]
        
        all_data = []
        for ticker in etfs:
            print(f"Téléchargement de {ticker} (Euros)...")
            
            # On prend le max d'historique disponible
            df = yf.download(ticker, period="max", interval="1d", auto_adjust=True)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if not df.empty:
                # Calculs Indicateurs
                df['MA_50'] = df['Close'].rolling(window=50).mean()
                df['MA_200'] = df['Close'].rolling(window=200).mean()
                df['Symbol'] = ticker
                df = df.dropna()
                all_data.append(df)
            else:
                print(f"⚠️ Aucune donnée trouvée pour {ticker}")

        if all_data:
            final_df = pd.concat(all_data)
            
            # 3. ÉCRASEMENT DE LA TABLE (REPLACE)
            # Important car on change de devise ($ -> €), on ne peut pas mélanger.
            final_df.to_sql('etf_prices', engine, if_exists='replace')
            print("Base de données mise à jour avec les ETF Européens.")
        else:
            print("Erreur : Aucun ETF n'a pu être téléchargé.")

    task_etl = PythonOperator(
        task_id='extract_transform_load_etf_euro',
        python_callable=etl_process
    )

    task_etl