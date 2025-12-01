# Data Engineering Pipeline - ETF Analysis

An End-to-End Data Engineering project built with Docker, PostgreSQL, Python, and Streamlit.

## 🎯 Objective
To build an automated pipeline that retrieves historical price data for 3 major ETFs (SPY, QQQ, IWM), stores the data in a local Data Warehouse, and visualizes comparative performance over a 30-year period.

## 🛠 Tech Stack
* **Containerization:** Docker & Docker Compose
* **ETL:** Python (Pandas, SQLalchemy, Yfinance)
* **Database:** PostgreSQL
* **Visualization:** Streamlit & Plotly

## 🚀 How to Run
1.  Clone the repository.
2.  Start the services: `docker-compose up -d --build`
3.  Access the Dashboard: `http://localhost:8501`
4.  Access the Database via PgAdmin: `http://localhost:8080`