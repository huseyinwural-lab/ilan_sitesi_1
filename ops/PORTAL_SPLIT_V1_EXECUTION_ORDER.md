# PORTAL_SPLIT_V1_EXECUTION_ORDER

## Risk Azaltıcı Uygulama Sırası

1) **BackofficePortalApp oluştur + admin route’ları taşı**
- Admin layout ve admin sayfalar backoffice portal modülünde import edilir.

2) **DealerPortalApp oluştur + minimal route seti**
- Dealer shell + placeholder.

3) **PortalGate’i router seviyesine yerleştir**
- Lazy import tetiklenmeden önce guard PASS/FAIL.

4) **Login route’larını ayır + post-login redirect matrisi**
- `/login`, `/dealer/login`, `/admin/login`

5) **Demo credentials prod gizleme**
- ENV ile kontrol

6) **Regression smoke + kanıt paketi**
- Public home/search
- Login’ler
- Wrong role negatif test network kanıtı
