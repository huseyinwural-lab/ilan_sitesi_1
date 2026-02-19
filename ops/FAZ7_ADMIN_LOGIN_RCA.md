## FAZ-7 Admin Login RCA

- **Kök neden (tek cümle):** Backend servisinin `submit_vehicle_listing` fonksiyonunda parametre sıralama hatası (non-default argument after default) nedeniyle çökmesi, login sonrası admin shell’in yüklenmesini engelledi.
- **Kanıt (log):** `/var/log/supervisor/backend.err.log` içinde `SyntaxError: non-default argument follows default argument` (server.py:5064).

## Düzeltme

- Endpoint parametre sıralaması düzeltildi, backend yeniden ayağa kalktı.