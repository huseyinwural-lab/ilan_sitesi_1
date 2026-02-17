# Router Convention

## 1. Prensip
`/api/v1/me` namespace'i altındaki tüm endpointler:
1.  **Authenticated**: Mutlaka `current_user` gerektirir.
2.  **Self-Service**: Kullanıcının *kendi* verisi üzerinde işlem yapar.
3.  **No-Admin**: Admin yetkisi gerektiren işlemler (örn. kullanıcıyı banlama) burada yer almaz (`/api/v1/admin/users` altındadır).

## 2. Dosya Yapısı
*   `app/routers/user_panel/me.py`: Ana profil işlemleri.
*   `app/routers/user_panel/security.py`: Şifre, 2FA, cihaz yönetimi.
