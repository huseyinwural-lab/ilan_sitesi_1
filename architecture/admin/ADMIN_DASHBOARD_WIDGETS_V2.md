# ADMIN_DASHBOARD_WIDGETS_V2 — Ops Panel Widget Seti

## Zorunlu Widget’lar
1) **Aktif ilan sayısı**
- Total
- Country (Country mode)

2) **Bekleyen moderasyon**
- Moderation Queue pending count

3) **Aktif dealer**
- Aktif dealer sayısı (country + total)

4) **Son 24 saat etkinlik**
- search count
- detail view count
- reveal (phone/email) count

5) **Sistem Sağlığı**
- 5xx oranı
- p95 latency

6) **Fraud/Spam**
- Flag sayısı

## Veri Kaynakları (MVP)
Bu repo’da şu an kısıtlı API seti bulunduğu için:
- İlk iterasyonda widget’lar UI’da yer alır.
- Veri kaynağı olmayan metrikler "coming soon" / placeholder olabilir.
- İkinci iterasyonda tek bir admin metrics endpoint’i ile gerçek sayım yapılır.
