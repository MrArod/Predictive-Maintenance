# Predictive Maintenance & KPI Dashboard

## 🚀 Project Overview
This project aims to build a **predictive maintenance system** using **machine learning and data analytics**. The system will:
- Store and process turbine engine sensor data.
- Predict engine failure using RUL calculations.
- Provide real-time KPIs through Power BI & Tableau dashboards.

## 📌 Project Structure
- **SQL Database**: Data storage, preprocessing, and querying.
- **EDA & Feature Engineering**: Sensor analysis and ML feature extraction.
- **Predictive Models**: RUL prediction using XGBoost & Random Forest.
- **KPI Dashboard**: Power BI/Tableau visualization for insights.

## **🔹 Data Sources & Methodologies**

| **Component** | **Methodology** | **Data Sources** | **Tools Used** |
| --- | --- | --- | --- |
| **Data Ingestion** | Convert NASA C-MAPSS `.txt` data to structured SQL tables. | NASA Turbofan Sensor Data (C-MAPSS) | Python (Pandas), SQL (PostgreSQL) |
| **Data Cleaning & Structuring** | Handle missing values, standardize types, index data for fast queries. | Preprocessed Sensor Readings | SQL, Python (Pandas) |
| **Failure Threshold Estimation** | Calculate statistical anomaly thresholds (95th percentile) & health index functions. | Sensor readings (temperature, pressure, speed) | SQL (PERCENTILE_CONT), Python (Z-score, IQR) |
| **Remaining Useful Life (RUL) Prediction** | Compute RUL dynamically based on last recorded cycles per engine. | Time-series cycles per engine | Python (Pandas), SQL |
| **Predictive Maintenance Model** | Machine Learning (XGBoost, Random Forest) on sensor degradation trends. | Historical failure data | Python (Scikit-learn) |
| **KPI Dashboard & Reporting** | Aggregate trends, visualize real-time failure predictions. | SQL-queried data | Power BI, Tableau |

## **🔹 Key Performance Indicators (KPIs)**

| **Metric** | **Definition** | **Purpose** |
| --- | --- | --- |
| **Production Efficiency (%)** | (Actual Output / Expected Output) × 100 | Tracks overall engine performance. |
| **Failure Rate (%)** | (Failed Engines / Total Engines) × 100 | Measures reliability of maintenance cycles. |
| **Mean Time to Failure (MTTF)** | Avg. cycles before engine failure | Estimates expected operational life. |
| **Remaining Useful Life (RUL)** | Cycles left before failure | Enables predictive maintenance. |
| **Downtime Cost ($/hr)** | Unplanned downtime cost per failure event | Justifies ROI of predictive maintenance. |

## 🛠 Tech Stack & Tools
- **SQL (PostgreSQL, MySQL)** → Data storage & processing
- **Python (Pandas, NumPy, Scikit-learn)** → Data analysis & ML modeling
- **Power BI / Tableau** → Dashboard visualization
- **Docker & API** → Deployment & accessibility

## 🚢 Running the API & Frontend Stack

The repository ships with a FastAPI service (`deployment/API_endpoint.py`) and a Streamlit UI (`frontend/streamlit_app.py`). Both
components are packaged together through the Dockerfile in `deployment/`.

### Prerequisites

- Docker 24+
- (Optional) An external SQL database that exposes the `engine_predictions`, `kpi_trends`, and `kpi_aggregates` tables/views. If not
  supplied the stack falls back to the bundled sample dataset located at `deployment/sample_data.json`.

### Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `PREDICTIVE_API_KEY` | Shared secret expected in the `X-API-Key` header for `/predict`, `/metrics`, `/reload`. | `dev-secret` |
| `PREDICTIVE_API_BASE_URL` | Base URL the Streamlit client uses to reach the API. | `http://localhost:8000` |
| `DATABASE_URL` | Optional SQLAlchemy connection string for production data. | *(unset)* |

### Build & Run with Docker

```bash
docker build -t predictive-maintenance -f deployment/Dockerfile .
docker run \
  -p 8000:8000 \
  -p 8501:8501 \
  -e PREDICTIVE_API_KEY="your-strong-secret" \
  -e PREDICTIVE_API_BASE_URL="http://localhost:8000" \
  predictive-maintenance
```

- The FastAPI service is exposed at **http://localhost:8000** (health check at `/health`).
- The Streamlit dashboard is available at **http://localhost:8501**.

To point the service at a managed database, supply a `DATABASE_URL` (e.g. `postgresql+psycopg://user:pass@host:5432/db`). The
expected schema is documented in `deployment/API_endpoint.py`.

### Authenticating Requests

All non-health endpoints require an API key supplied through the `X-API-Key` header. Use the same secret for local development and
the container runtime:

```bash
curl \
  -H "X-API-Key: your-strong-secret" \
  http://localhost:8000/predict
```

If a key is not provided or mismatched, the service returns **401 Unauthorized**.

### Local Development

To run the stack without Docker make sure the dependencies in `deployment/requirements.txt` are installed, then execute in separate
terminals:

```bash
uvicorn deployment.API_endpoint:app --reload --port 8000
streamlit run frontend/streamlit_app.py --server.port 8501
```

Update the `PREDICTIVE_API_BASE_URL` environment variable if the API is hosted elsewhere.

## 📝 Documentation & Portfolio Links
- **[GitHub Repository](#)** (Code & Implementation)
- **[Power BI/Tableau Dashboard](#)** (Live KPI Dashboard)
- **[Business Impact Report](#)** (Financial Justification)

## 👨‍💻 Author
**Anthony Rodriguez**  
🔗 [LinkedIn Profile](#)  
📧 [Email](#)

## 📜 License
This project is licensed under the **MIT License**.

