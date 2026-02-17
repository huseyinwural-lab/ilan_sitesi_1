# Public Dealer Profile URL Spec

## 1. URL Pattern
To maximize SEO and brand visibility:
`https://platform.com/bayi/{dealer_slug}`

### Examples
*   `/bayi/schmidt-automobile`
*   `/bayi/istanbul-emlak-merkezi`

## 2. Routing Rules
*   **Slug Uniqueness**: Guaranteed by `Dealer` model.
*   **Case Sensitivity**: Case-insensitive (lowercase preferred).
*   **404 Behavior**: If slug not found or Dealer not active -> 404 Page.

## 3. SEO Metadata
*   **Title**: `{Company Name} - {City} | {Platform Name}`
*   **Description**: `{Company Name} listings. Contact: {Phone}. Address: {City}.`
*   **Canonical**: Self.
*   **Structured Data**: `LocalBusiness` schema.
