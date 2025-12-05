> ⏳ **Wait ~60 seconds** for Airflow to initialize the database and create the admin user automatically.

### 3. Trigger the Data Ingestion
1.  Go to Airflow: [http://localhost:8080](http://localhost:8080)
2.  Login with the credentials below.
3.  Toggle the DAG `etf_pipeline_v2_avec_indicateurs` to **ON** (Blue switch).
4.  Click the **Play ▶️** button (Trigger DAG) to download the historical data (since 2005).

### 4. Open the Trading Station
Go to: [http://localhost:8501](http://localhost:8501)

---

## 🔑 Access & Credentials

Everything is pre-configured. Use these logins:

| Service | URL | Login | Password | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Airflow UI** | [http://localhost:8080](http://localhost:8080) | `airflow` | `airflow` | Workflow Manager |
| **PgAdmin** | [http://localhost:5050](http://localhost:5050) | `admin@admin.com` | `root` | Database Admin |
| **Dashboard** | [http://localhost:8501](http://localhost:8501) | *(None)* | *(None)* | End-User App |
| **Postgres** | `localhost:5432` | `user_etf` | `password_etf` | (Internal Use) |

> **Note:** In PgAdmin, the server "Ma Base ETF" is already registered. You might need to re-enter the password (`password_etf`) upon first click for security reasons.

---

## ✨ Features Breakdown

### 🎓 Tab 1: The Assistant (Smart Analysis)
* **Verdict Engine:** Automatically analyzes **RSI** (Overbought/Oversold) and **Golden Crosses** (Trends) to give clear Buy/Sell signals (🟢/🔴).
* **Educational Mode:** Tooltips and Glossaries explain complex terms to beginners.
* **Annual Performance:** Bar chart showing yearly returns to visualize volatility.

### 📊 Tab 2: The Comparator
* Compare multiple assets (Stocks vs Bonds) on a normalized graph.
* Analyze **CAGR** (Compound Annual Growth Rate) over specific periods.

### 🔮 Tab 3: DCA Simulator (Backtesting)
* **Simulation:** "What if I invested 200€/month since 2015?"
* **Visual Proof:** Compares "Cash kept under mattress" vs "Invested Portfolio".
* **Reality Check:** Highlights the power of compound interest.

### 🇪🇺 Assets Tracked (European Optimized)
To avoid US Withholding Tax and simplify management, the pipeline tracks **Accumulating ETFs** (Dividends are reinvested automatically):
* **CSPX.AS:** iShares Core S&P 500 (Acc)
* **CNDX.AS:** iShares Nasdaq 100 (Acc)
* **ZPRR.DE:** SPDR Russell 2000 US Small Cap (Acc)
* **AGGH.AS:** iShares Global Aggregate Bond (Hedged)

---

## 🛡 Engineering Highlights (Automation)

This project implements **DevOps & Data Engineering best practices**:

1.  **DDL Management:** The table `etf_prices` is created automatically by Postgres (`init.sql`) on startup. The Dashboard never crashes due to missing tables.
2.  **Infrastructure as Code:** Airflow Connections are injected via Environment Variables (`AIRFLOW_CONN_...`). No manual setup required in the UI.
3.  **Persistence:** Docker Volumes (`postgres_data`, `pgadmin_data`) ensure data survives container restarts.
4.  **Robustness:** The ETL script uses `to_sql(if_exists='replace')` to be idempotent (can be re-run safely).

---

## 🧹 Maintenance Commands

**Stop the project:**
```bash
docker-compose down