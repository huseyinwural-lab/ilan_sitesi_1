# P16 Withdrawal Eligibility Rules (v1)

**Amaç:** Kullanıcıların hak ettikleri ve kesinleşmiş (risk barındırmayan) ödülleri çekebilmesini sağlamak, finansal zararı önlemek.

## 1. Temel Kurallar

### 1.1. Net Bakiye Hesabı (Net Balance Calculation)
Para çekme yetkisi sadece "Ledger" üzerindeki net bakiye üzerinden verilir.
*   **Formula:** `SUM(CREDIT) - SUM(DEBIT) - SUM(PAYOUT)`
*   `pending` statüsündeki ödüller bu hesaba **DAHİL EDİLMEZ**.

### 1.2. Blokaj Koşulları (Blocking Conditions)
Aşağıdaki durumlarda `can_withdraw` fonksiyonu `False` döner:
1.  **Negatif Bakiye:** Net bakiye < 0 ise. (Önceki çekimlerden sonra gelen refundlar nedeniyle borçlu olma durumu).
2.  **Minimum Tutar:** Talep edilen tutar veya toplam bakiye < 50 TRY ise.
3.  **Risk Flag:** Kullanıcı hesabı `is_flagged=True` ise (Abuse şüphesi).

## 2. Negatif Bakiye Yönetimi (Negative Balance Guard)
*   **Kural:** Platform, kullanıcıdan alacaklı duruma geçerse (Net Bakiye < 0), yeni ödül kazanımları otomatik olarak bu borcu kapatır (Mahsuplaşma).
*   **Aksiyon:** Admin dashboard'da bu kullanıcılar "Negative Balance Risk" listesinde gösterilir.

## 3. Atomic İşlem (Concurrency)
Withdraw işlemi sırasında:
1.  Veritabanı transaction'ı başlar.
2.  Kullanıcının ledger kayıtları `WITH FOR UPDATE` ile kilitlenir veya bakiye hesaplanır.
3.  Yeterli bakiye varsa `payout_ledger` kaydı oluşturulur.
4.  Transaction commit edilir.
