# Real Estate Attribute Options (TR/DE/FR)

**Logic:** All Select options are defined here. The Backend `AttributeOption` table must be seeded with these values and `sort_order`.

## 1. Room Count (`room_count`)
*Used in Residential.*

| Sort | Value | TR | DE | FR |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `1+0` | Stüdyo (1+0) | Studio (1 Zimmer) | Studio (T1) |
| 2 | `1+1` | 1+1 | 2 Zimmer | T2 |
| 3 | `2+1` | 2+1 | 3 Zimmer | T3 |
| 4 | `2.5+1`| 2.5+1 | 3.5 Zimmer | - |
| 5 | `3+1` | 3+1 | 4 Zimmer | T4 |
| 6 | `3.5+1`| 3.5+1 | 4.5 Zimmer | - |
| 7 | `4+1` | 4+1 | 5 Zimmer | T5 |
| 8 | `4+2` | 4+2 | 6 Zimmer | T6 |
| 9 | `5+1` | 5+1 | 6+ Zimmer | T7+ |
| 10 | `5+2` | 5+2 | - | - |
| 11 | `6+` | 6+ Oda | Mehr als 6 | Plus de 6 |

## 2. Building Status (`building_status`)
*Used Global.*

| Sort | Value | TR | DE | FR |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `new` | Sıfır (Yeni) | Neubau | Neuf |
| 2 | `used` | İkinci El | Altbau | Ancien |
| 3 | `construction` | Yapım Aşamasında | Im Bau | En construction |

## 3. Heating Type (`heating_type`)
*Used Global.*

| Sort | Value | TR | DE | FR |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `combi_gas` | Kombi (Doğalgaz) | Gas-Etagenheizung | Chauffage au gaz |
| 2 | `central` | Merkezi | Zentralheizung | Chauffage central |
| 3 | `central_share`| Merkezi (Pay Ölçer) | Zentral (Zähler) | Central (Compteur) |
| 4 | `electric` | Elektrikli Radyatör | Elektroheizung | Électrique |
| 5 | `floor` | Yerden Isıtma | Fußbodenheizung | Chauffage au sol |
| 6 | `heat_pump` | Isı Pompası | Wärmepumpe | Pompe à chaleur |
| 7 | `stove` | Soba | Ofenheizung | Poêle |
| 8 | `none` | Yok | Keine | Aucune |

## 4. Floor Location (`floor_location`)
*Used Residential.*

| Sort | Value | TR | DE | FR |
| :--- | :--- | :--- | :--- | :--- |
| 0 | `basement` | Bodrum | Keller | Sous-sol |
| 1 | `ground` | Giriş / Zemin | Erdgeschoss | Rez-de-chaussée |
| 2 | `garden` | Bahçe Katı | Gartengeschoss | Rez-de-jardin |
| 3 | `high_entrance`| Yüksek Giriş | Hochparterre | - |
| 4 | `1` | 1. Kat | 1. Etage | 1er étage |
| 5 | `2` | 2. Kat | 2. Etage | 2ème étage |
| 6 | `3` | 3. Kat | 3. Etage | 3ème étage |
| 7 | `4` | 4. Kat | 4. Etage | 4ème étage |
| 8 | `5-10` | 5-10. Kat Arası | 5.-10. Etage | 5-10ème étage |
| 9 | `10+` | 10. Kat Üzeri | Ab 10. Etage | 10ème étage + |
| 10 | `penthouse` | Çatı Katı | Dachgeschoss | Dernier étage |

## 5. Ground Survey (`ground_survey`)
*Used Commercial.*

| Sort | Value | TR | DE | FR |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `done` | Yapıldı | Durchgeführt | Effectué |
| 2 | `not_done` | Yapılmadı | Nicht durchgeführt | Non effectué |
