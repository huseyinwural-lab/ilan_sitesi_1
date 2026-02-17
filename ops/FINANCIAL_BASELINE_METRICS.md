# Financial Baseline Metrics (v1)

**Amaç:** Büyüme fazında sistemin sağlığını ölçmek için referans değerler.

## 1. Operasyonel Metrikler
| Metrik | Baseline (Hedef) | Alarm Eşiği |
| :--- | :--- | :--- |
| **Revoke Rate** | <%2 (Tüm ödüllerin) | >%5 |
| **Negative Balance Users** | 0 | >0 |
| **Webhook Error Rate** | <%0.1 | >%1 |
| **Avg. Confirmation Time** | 14 Gün | >15 Gün (Job gecikmesi) |

## 2. Finansal Metrikler
| Metrik | Baseline (Hedef) | Alarm Eşiği |
| :--- | :--- | :--- |
| **Refund/Reward Ratio** | <%5 | >%10 |
| **Ledger Mismatch** | 0.00 TRY | >1.00 TRY |
| **Chargeback Rate** | <%0.5 | >%1 |

## 3. Büyüme Metrikleri (P17 Hazırlığı)
*   **Reward/CAC:** Ödül maliyetinin müşteri edinme maliyetine oranı.
*   **Referral Viral Coefficient:** Bir kullanıcının getirdiği ortalama yeni kullanıcı sayısı.
