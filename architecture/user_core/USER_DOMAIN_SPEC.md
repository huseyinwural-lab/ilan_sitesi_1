# User Domain Spec

Bu doküman, kullanıcı veri modelinin "Tek Gerçek Kaynağı"dır (SSOT).

## 1. Alanlar

### 1.1. `user_type` (Enum)
*   **Kaynak**: P28 (Mevcut)
*   **Değerler**:
    *   `individual`: Bireysel kullanıcı. Varsayılan.
    *   `commercial`: Ticari satıcı (Galerici, Emlakçı).
*   **Kural**: `commercial` tipi, `dealer_profiles` tablosunda kayıt gerektirir (P28 kuralı).

### 1.2. `kyc_status` (Enum)
*   **Yeni Alan**
*   **Değerler**:
    *   `none`: Başvurulmadı. (Varsayılan)
    *   `pending`: Belge yüklendi, onay bekleniyor.
    *   `verified`: Onaylandı. (Rozet verilir)
    *   `failed`: Reddedildi.
*   **Kullanım**: `commercial` kullanıcılar için zorunlu (Soft Gate: İlan limitine takılır).

### 1.3. `default_country` (String)
*   **Yeni Alan**
*   **Değerler**: ISO 2-harf kodu (`DE`, `AT`, `CH`, `FR`).
*   **Varsayılan**: Kayıt sırasındaki IP veya seçim.
*   **Kullanım**: İlan verirken ve arama yaparken varsayılan filtre.

### 1.4. Doğrulama Bayrakları
*   `email_verified` (Bool): Kayıt sonrası e-posta linki ile.
*   `phone_verified` (Bool): SMS OTP ile.

## 2. İlişkiler
*   `User` 1-1 `DealerProfile` (Eğer `commercial` ise).
