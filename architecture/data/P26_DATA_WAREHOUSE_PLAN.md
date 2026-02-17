# Data Warehouse Plan

## 1. Architecture
*   **Source**: PostgreSQL (Transactional).
*   **Pipeline**: ETL (Extract-Transform-Load) via Airflow/dbt (Future).
*   **Destination**: Snowflake or BigQuery (or separate Postgres Analytics DB for MVP).

## 2. Schema (Star Schema)
*   **Fact Tables**: `fact_interactions`, `fact_transactions`.
*   **Dimension Tables**: `dim_users`, `dim_listings`, `dim_dates`, `dim_countries`.

## 3. Reporting Tool
*   **Tool**: Metabase or Looker Studio.
*   **Dashboards**:
    *   Executive Overview.
    *   Sales Performance.
    *   Product Usage.
