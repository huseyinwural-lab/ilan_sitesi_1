# CQA_BODY_TO_VEHICLE_TYPE_MAP_V1

## V1 Mapping
| CarQuery body | vehicle_type |
|---|---|
| SUV, Crossover | suv |
| Pickup | pickup |
| Truck | truck |
| Bus | bus |
| Offroad, 4x4 | offroad |
| Sedan, Coupe, Hatchback, Wagon, Convertible, Roadster, Minivan, Van | car |

## Notlar
- Body değerleri **case-insensitive** normalize edilir (lowercase, boşluk/özel karakter temizliği).
- Mapping dışında kalan body değerleri **unknown** sayılır ve importta engellenir.
