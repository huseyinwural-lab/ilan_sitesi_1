# P19 Country Resolver Spec (v1)

**Amaç:** Gelen isteğin hangi ülkeye ait olduğunu belirlemek ve URL yapısını (`/{country}/...`) zorunlu kılmak.

## 1. Algılama Mantığı (Detection Logic)

### A. URL Path Kontrolü (Priority 1)
*   İstek yolu `/api`, `/admin`, `/static` ile **başlamıyorsa**:
*   İlk segment (`path.split('/')[1]`) kontrol edilir.
*   Eğer bu segment geçerli bir `country_code` (TR, DE, FR vb.) ise:
    *   `request.state.country` = `CODE`.
    *   İşlem devam eder.

### B. Otomatik Yönlendirme (Redirection)
*   Eğer ilk segment geçerli bir ülke kodu **değilse**:
    *   Kullanıcının ülkesini tahmin et (Header `CF-IPCountry` veya `Accept-Language` veya Default `TR`).
    *   Yeni URL oluştur: `/{detected_country}{original_path}`.
    *   **307 Temporary Redirect** (Test/Dev aşaması için).
    *   **301 Permanent Redirect** (Prod - SEO için).

## 2. Kapsam Dışı (Exclusions)
Aşağıdaki yollar bu middleware tarafından **etkilenmemelidir**:
*   `/api/*`
*   `/admin/*`
*   `/static/*`
*   `/favicon.ico`
*   `/sitemap.xml` (Kök sitemap)
*   `/robots.txt`

## 3. Context Injection
*   Middleware, doğrulanan ülke kodunu `request.state.country` içine ve `X-Country-Code` response header'ına ekler.
