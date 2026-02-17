# DB Read Replica Scaling Plan

## 1. Architecture
*   **Primary (Master)**: Handles Writes (User, Listing Create, Message Send).
*   **Replica (Read-Only)**: Handles High-Volume Reads (Search, Feed, Public Profile).

## 2. Connection Pool Routing
*   **Application Logic**:
    *   `get_db_write()`: Returns session connected to Master.
    *   `get_db_read()`: Returns session connected to Replica (Round-robin if multiple).

## 3. Config
*   `DATABASE_URL_PRIMARY`
*   `DATABASE_URL_REPLICA`

## 4. Replication Lag
*   **Tolerance**: Search results can be 1-2 seconds behind.
*   **Critical Paths**: "My Listings" and "Messages" must use Primary to ensure "Read-Your-Writes" consistency.
