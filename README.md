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

