# 🚀 End-to-End Data Engineering Pipeline (V2)

An automated Data Engineering project that orchestrates the extraction, transformation, and visualization of financial data using **Apache Airflow**, **Docker**, and **PostgreSQL**.

## 🎯 Objective
To build a robust pipeline that:
1.  **Extracts** daily stock data for major ETFs (SPY, QQQ, IWM).
2.  **Transforms** data by calculating Technical Indicators (Moving Averages MA50 & MA200).
3.  **Loads** clean data into a PostgreSQL Data Warehouse.
4.  **Visualizes** insights via an interactive Dashboard (Performance comparison & Golden Cross strategy).

## 🛠 Tech Stack & Architecture
* **Orchestration:** Apache Airflow (running on Python 3.9)
* **Containerization:** Docker & Docker Compose
* **Database:** PostgreSQL (v15)
* **ETL:** Python (Pandas, SQLalchemy, Yfinance)
* **Visualization:** Streamlit & Plotly

## 📊 Features
* **Automated Pipeline:** Airflow DAG scheduled to run daily after market close.
* **Technical Analysis:** Automatic calculation of 50-day and 200-day Moving Averages.
* **Interactive Dashboard:**
    * *Tab 1:* Multi-ETF Performance Comparator.
    * *Tab 2:* Technical Analysis (Price vs Moving Averages).

## 🚀 How to Run
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/MarvingBaloo/etf-data-pipeline.git](https://github.com/MarvingBaloo/etf-data-pipeline.git)
    cd etf-data-pipeline
    ```

2.  **Start the infrastructure:**
    ```bash
    docker-compose up -d --build
    ```
    *(First launch may take a few minutes to initialize Airflow).*

3.  **Access the services:**

| Service | URL | Credentials (User/Pass) |
| :--- | :--- | :--- |
| **Airflow UI** | http://localhost:8080 | `airflow` / `airflow` |
| **Streamlit Dashboard** | http://localhost:8501 | *(No login required)* |
| **PgAdmin (DB GUI)** | http://localhost:5050 | `admin@admin.com` / `root` |

4.  **Trigger the Pipeline:**
    * Go to Airflow UI.
    * Activate the DAG `etf_pipeline_v2_avec_indicateurs`.
    * Click the "Play" button to trigger the first run.