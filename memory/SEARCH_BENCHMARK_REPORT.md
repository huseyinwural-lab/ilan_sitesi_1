# Search Benchmark Report (Mongo vs Postgres)

**Amaç:** Search latency ve query plan karşılaştırması

## Env
- Dataset boyutu: ________
- Mongo versiyon: ________
- Postgres versiyon: ________

## Senaryolar
1) Text search (title/description)
2) Facet (category + price)
3) Multi-filter (category + city + price)
4) Sorting (price_desc, date_desc)

## Sonuç Tablosu
| Scenario | Mongo p50 | Mongo p95 | Postgres p50 | Postgres p95 | Notes |
| --- | --- | --- | --- | --- | --- |
| Text search | TBD | TBD | TBD | TBD | |
| Facet (category+price) | TBD | TBD | TBD | TBD | |
| Multi-filter | TBD | TBD | TBD | TBD | |
| Sorting | TBD | TBD | TBD | TBD | |

## EXPLAIN ANALYZE (Postgres)
- Query 1:
```
TBD
```
- Query 2:
```
TBD
```

## Notlar
- Index kullanım oranı
- p95 high latency root cause (if any)
