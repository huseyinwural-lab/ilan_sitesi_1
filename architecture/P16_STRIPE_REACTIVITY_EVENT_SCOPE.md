# P16 Stripe Reactivity Event Scope (v1)

**Amaç:** Finansal reaktivite için dinlenecek ve işlenecek Stripe Webhook olaylarının kapsamını belirlemek.

## 1. Zorunlu Olaylar (Minimum Viable Scope)

| Event Tipi | Tetikleyici | Sistemdeki Etkisi |
| :--- | :--- | :--- |
| `charge.refunded` | Bir ödemenin tamamı veya bir kısmı iade edildiğinde. | Ödül (Reward) geri alınır (Revocation). Ledger'a borç (Debit) işlenir. |
| `charge.dispute.created` | Müşteri ödemeye itiraz ettiğinde (Chargeback). | Ödül "Riskli" olarak işaretlenir. Henüz geri alınmaz (Policy: Dispute Created = At-Risk). |
| `charge.dispute.closed` | İtiraz süreci sonuçlandığında. | Eğer sonuç `lost` (kayıp) ise, ödül geri alınır. `won` (kazanıldı) ise işlem yapılmaz. |

## 2. Opsiyonel / İleri Seviye Olaylar (Backlog)

*   `refund.created`: Refund nesnesi oluşturulduğunda. (Şimdilik `charge.refunded` yeterli, çünkü işlem tamamlanınca tetikleniyor).
*   `invoice.payment_failed`: Yinelenen abonelik ödemesi başarısız olduğunda. (Şu anki sistemde ödül sadece `invoice.paid` ile verildiği için, başarısız ödemede zaten ödül verilmez. Ancak "pending" bir ödül varsa ve ödeme sonradan başarısız olursa -ki nadirdir- bu event ile iptal edilebilir).

## 3. Scope Dışı
*   `charge.succeeded`: Zaten `checkout.session.completed` veya `invoice.paid` üzerinden ele alınıyor.
*   `customer.subscription.updated`: Plan değişiklikleri (Upgrade/Downgrade) şu an reward hesaplamasını etkilemiyor (MVP: İlk ödeme kuralı).
