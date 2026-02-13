# Vehicle Master Data Sources ADR v1

**Decision:** Hybrid Source Strategy (Primary: Open/Public Data, Secondary: Manual/Commercial)

## 1. "Up-to-Date" Definition
-   **Frequency:** Monthly Sync.
-   **Latency:** New models appear within 30 days of market launch.
-   **Hotfix:** Immediate manual entry via Admin Panel for critical missing models.

## 2. Source Strategy
### A. Primary: Public Datasets (NHTSA / EU Open Data)
-   **Pros:** Free, structured.
-   **Cons:** US-centric (NHTSA), might miss EU trims.
-   **Usage:** Base population.

### B. Secondary: Web Scraper / Aggregator (Controlled)
-   **Target:** Major Auto Portals (Mobile.de / AutoScout24 public filters).
-   **Method:** Periodic diff check (List of models).
-   **License:** *Strictly observational usage (Fair Use).* We only sync "Names", not content.

### C. Fallback: Manual Admin
-   **Scenario:** Customer complains "My car model is missing".
-   **Action:** Support adds it instantly via Admin UI.

## 3. Quality Metrics
-   **Coverage:** > 95% of market listings map to a known Model.
-   **Duplicate Rate:** < 0.1% (Strict slug uniqueness).
-   **Stale Rate:** < 5% (Models not updated in > 5 years).
