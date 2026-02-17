# L2: Paid Traffic Test Plan

## 1. Objective
To validate conversion metrics (View -> Lead) with controlled, high-intent traffic.

## 2. Campaign Structure

### 2.1. Google Ads (Search)
*   **Keywords**: "Satılık daire Berlin", "Turkish real estate Germany", "Berlin emlak".
*   **Target**: Germany (Turkish Speakers).
*   **Budget**: €50 / day.
*   **Landing Page**: `/de/emlak/konut/satilik/daire/berlin` (Programmatic SEO Page).

### 2.2. Facebook/Instagram (Retargeting)
*   **Audience**: Visitors who viewed > 2 listings but didn't convert.
*   **Creative**: Carousel of viewed properties.
*   **Budget**: €20 / day.

## 3. Success Metrics (Cost Per Result)
*   **CPC (Cost Per Click)**: < €0.50.
*   **CPL (Cost Per Lead)**: < €5.00.
*   **Reveal Rate**: > 2%.

## 4. Setup
*   **UTM Tags**: `?utm_source=google&utm_medium=cpc&utm_campaign=launch_de`.
*   **Conversion Tracking**: Fire GTM event on "Reveal Button" click.
