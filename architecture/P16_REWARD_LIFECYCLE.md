# P16 Reward Lifecycle Policy (v1)

**Amaç:** Referral ödüllerinin finansal güvenliğini sağlamak ve iade/itiraz risklerini yönetmek.

## 1. Statüler (States)

| Statü | Tanım | Bakiye Etkisi | Geçiş Koşulu |
| :--- | :--- | :--- | :--- |
| **Pending** | Ödül hak edildi ancak henüz kesinleşmedi. | Yok (Blockajlı) | `invoice.paid` |
| **Confirmed** | Ödül kesinleşti ve kullanılabilir. | +Credit | 14 gün süre dolumu (Dispute window) |
| **Revoked** | Ödül iptal edildi. | -Debit | Refund veya Dispute Lost |
| **Applied** | (Legacy) Eski sistemden kalanlar. | +Credit | Migration sonrası `confirmed` sayılır. |

## 2. Yaşam Döngüsü (Lifecycle)

### A. Kazanım (Earning)
1.  Referee ödeme yapar (`invoice.paid`).
2.  Sistem `ReferralReward` kaydını `pending` statüsünde oluşturur.
3.  Kullanıcı panelinde "Bekleyen Ödül" olarak görünür.

### B. Kesinleşme (Confirmation)
1.  Her gece çalışan `process_reward_maturity.py` job'ı, 14 günü dolduran `pending` ödülleri tarar.
2.  Statü `confirmed` yapılır.
3.  `RewardLedger` tablosuna "CREDIT" kaydı atılır.
4.  Stripe Customer Balance güncellenir (Negatif bakiye yani kredi eklenir).

### C. İptal (Revocation)
1.  Stripe'dan `charge.refunded` veya `charge.dispute.created` webhook'u gelir.
2.  İlgili ödül bulunur.
3.  Eğer `pending` ise -> Direkt `revoked` yapılır. Bakiye etkilenmez.
4.  Eğer `confirmed` ise -> `revoked` yapılır. `RewardLedger` tablosuna "DEBIT" kaydı atılır. Stripe Customer Balance'dan düşülür (Pozitif bakiye yani borç eklenir).

## 3. Negatif Bakiye Politikası
*   Eğer kullanıcının kredisi geri alındığında bakiye pozitife (borçlu duruma) geçerse, bir sonraki ödemesinde bu tutar tahsil edilir.
*   Withdrawal (Para çekme) talepleri, bakiye borçlu ise bloklanır.
