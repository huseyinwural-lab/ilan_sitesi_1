# P22: Revenue-Aware ML Objective & Fairness

## 1. Objective Function Evolution
Instead of optimizing purely for Click-Through Rate (CTR), we will optimize for **Expected Value (eV)**.

### 1.1. Formula
`Score = P(Click) * w1 + P(Conversion) * w2 * Value`

Where:
*   `P(Click)`: Probability of click (from CTR model).
*   `P(Conversion)`: Probability of contact/lead.
*   `Value`: Potential revenue from this action (e.g., Sponsored Click = $0.50, Lead = $5.00).

### 1.2. Implementation (Gradient Boosting)
We will use **Sample Weights** during training.
*   `listing_viewed`: Weight = 1 (Negative)
*   `listing_clicked`: Weight = 1 (Positive)
*   `listing_contacted`: Weight = 10 (Positive)
*   `sponsored_click`: Weight = 2 (Positive)

## 2. Fairness Constraints
To prevent the feed from becoming 100% ads (which kills retention), we enforce constraints.

### 2.1. Logic
*   **Max Sponsored Density**: Max 1 sponsored item per 5 organic items.
*   **Diversity**: Max 2 items from the same category consecutively.

### 2.2. Re-Ranking Algorithm (Post-Process)
1.  Take Top 100 items from ML Model.
2.  Iterate and fill slots:
    *   Slot 1: Best Score.
    *   Slot 2: Best Score (excluding Slot 1 category if possible).
    *   Slot 3: Best Score.
    *   Slot 4: Best Sponsored Item (if Score > Threshold).

## 3. Long-Term Retention Metric (LTV)
We must monitor if Revenue Optimization hurts retention.
*   **Metric**: `Day-30 Retention Rate` per Experiment Group.
*   **Guardrail**: If Revenue B > Revenue A (+10%) BUT Retention B < Retention A (-5%), **REJECT**.

## 4. Action Plan
1.  Update `extract_training_data.py` to include `sample_weight` column.
2.  Implement `FairnessReRanker` class in `MLServingService`.
