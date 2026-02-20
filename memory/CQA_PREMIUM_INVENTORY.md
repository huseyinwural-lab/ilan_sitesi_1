# CQA_PREMIUM_INVENTORY

## Zip İçeriği
- **CQA_Premium.csv** (CSV)
  - Boyut: 21,517,582 bytes
  - Satır sayısı: 81,135
  - Kolon sayısı: 37
  - Kolonlar: model_id, model_make_id, model_name, model_trim, model_year, model_body, model_engine_position, model_engine_cc, model_engine_cyl, model_engine_type, model_engine_valves_per_cyl, model_engine_power_ps, model_engine_power_rpm, model_engine_torque_nm, model_engine_torque_rpm, model_engine_bore_mm, model_engine_stroke_mm, model_engine_compression, model_engine_fuel, model_top_speed_kph, model_0_to_100_kph, model_drive, model_transmission_type, model_seats, model_doors, model_weight_kg, model_length_mm, model_width_mm, model_height_mm, model_wheelbase_mm, model_lkm_hwy, model_lkm_mixed, model_lkm_city, model_fuel_cap_l, model_sold_in_us, model_co2, model_make_display
  - Örnek satırlar (ilk 3):

```
2, abarth, 1300, Scorpione Coupe, 1968, Coupe, Rear, 1280, 4, in-line, NULL, 74, 6000, 108, 3000, 75.5, 71.5, 10.5:1, NULL, 185
3, abarth, 750, Saloon, 1956, NULL, Rear, 747, 4, in-line, NULL, 42, 5500, 54, NULL, 61.0, 64.0, 9.0:1, Gasoline, 150
4, abarth, OT, Berlina, 1964, NULL, Rear, 1591, 4, in-line, NULL, 156, 7600, NULL, NULL, 86.0, 68.5, 9.5:1, NULL, 220
```

- **CQA_Premium.sql** (SQL)
  - Boyut: 22,254,509 bytes
  - INSERT statement sayısı: 444
  - CREATE TABLE satırı: CREATE TABLE `tbl_models` (
  - İlk 5 satır:

```
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

```