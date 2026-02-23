# Search Parity Report (Mongo vs Postgres)
Generated at: 2026-02-23T12:36:38.564776Z

Mongo listing count: 0
Postgres listings_search count: 0

## Golden Query Set (50)
- Q01: q=araba | category=1debb8f9-cb41-47bf-8e6a-4fcc0423b9ec | city=Berlin | price=0-1000 | sort=newest
- Q02: q=- | category=cfcae39a-0287-471c-8944-8f4eab81fd24 | city=Munich | price=1000-5000 | sort=price_asc
- Q03: q=kiralik | category=1922d021-2a55-44be-84d4-a290f738ac7b | city=Hamburg | price=5000-20000 | sort=price_desc
- Q04: q=- | category=86dbd8d2-0148-4977-ac01-8dbd947024b4 | city=Ankara | price=20000-50000 | sort=newest
- Q05: q=daire | category=775bdf32-9df4-4f2a-b15f-8801f5c775f8 | city=Istanbul | price=50000-100000 | sort=price_asc
- Q06: q=- | category=bee9684b-5047-47f2-8499-7891f80c25e5 | city=Izmir | price=0-1000 | sort=price_desc
- Q07: q=bmw | category=835ca551-6fe0-463b-9634-4181d6feccd4 | city=Cologne | price=1000-5000 | sort=newest
- Q08: q=- | category=93ae26a7-fdd9-43ba-8143-60cbe5d5b44e | city=Frankfurt | price=5000-20000 | sort=price_asc
- Q09: q=ford | category=0a36ca7c-be80-4c1f-b2b9-6c4e29b12f67 | city=Stuttgart | price=20000-50000 | sort=price_desc
- Q10: q=- | category=81cb06c4-96c5-40cf-9343-1f0eed9756c8 | city=Dusseldorf | price=50000-100000 | sort=newest
- Q11: q=araba | category=1debb8f9-cb41-47bf-8e6a-4fcc0423b9ec | city=Berlin | price=0-1000 | sort=price_asc
- Q12: q=- | category=cfcae39a-0287-471c-8944-8f4eab81fd24 | city=Munich | price=1000-5000 | sort=price_desc
- Q13: q=kiralik | category=1922d021-2a55-44be-84d4-a290f738ac7b | city=Hamburg | price=5000-20000 | sort=newest
- Q14: q=- | category=86dbd8d2-0148-4977-ac01-8dbd947024b4 | city=Ankara | price=20000-50000 | sort=price_asc
- Q15: q=daire | category=775bdf32-9df4-4f2a-b15f-8801f5c775f8 | city=Istanbul | price=50000-100000 | sort=price_desc
- Q16: q=- | category=bee9684b-5047-47f2-8499-7891f80c25e5 | city=Izmir | price=0-1000 | sort=newest
- Q17: q=bmw | category=835ca551-6fe0-463b-9634-4181d6feccd4 | city=Cologne | price=1000-5000 | sort=price_asc
- Q18: q=- | category=93ae26a7-fdd9-43ba-8143-60cbe5d5b44e | city=Frankfurt | price=5000-20000 | sort=price_desc
- Q19: q=ford | category=0a36ca7c-be80-4c1f-b2b9-6c4e29b12f67 | city=Stuttgart | price=20000-50000 | sort=newest
- Q20: q=- | category=81cb06c4-96c5-40cf-9343-1f0eed9756c8 | city=Dusseldorf | price=50000-100000 | sort=price_asc
- Q21: q=araba | category=1debb8f9-cb41-47bf-8e6a-4fcc0423b9ec | city=Berlin | price=0-1000 | sort=price_desc
- Q22: q=- | category=cfcae39a-0287-471c-8944-8f4eab81fd24 | city=Munich | price=1000-5000 | sort=newest
- Q23: q=kiralik | category=1922d021-2a55-44be-84d4-a290f738ac7b | city=Hamburg | price=5000-20000 | sort=price_asc
- Q24: q=- | category=86dbd8d2-0148-4977-ac01-8dbd947024b4 | city=Ankara | price=20000-50000 | sort=price_desc
- Q25: q=daire | category=775bdf32-9df4-4f2a-b15f-8801f5c775f8 | city=Istanbul | price=50000-100000 | sort=newest
- Q26: q=- | category=bee9684b-5047-47f2-8499-7891f80c25e5 | city=Izmir | price=0-1000 | sort=price_asc
- Q27: q=bmw | category=835ca551-6fe0-463b-9634-4181d6feccd4 | city=Cologne | price=1000-5000 | sort=price_desc
- Q28: q=- | category=93ae26a7-fdd9-43ba-8143-60cbe5d5b44e | city=Frankfurt | price=5000-20000 | sort=newest
- Q29: q=ford | category=0a36ca7c-be80-4c1f-b2b9-6c4e29b12f67 | city=Stuttgart | price=20000-50000 | sort=price_asc
- Q30: q=- | category=81cb06c4-96c5-40cf-9343-1f0eed9756c8 | city=Dusseldorf | price=50000-100000 | sort=price_desc
- Q31: q=araba | category=1debb8f9-cb41-47bf-8e6a-4fcc0423b9ec | city=Berlin | price=0-1000 | sort=newest
- Q32: q=- | category=cfcae39a-0287-471c-8944-8f4eab81fd24 | city=Munich | price=1000-5000 | sort=price_asc
- Q33: q=kiralik | category=1922d021-2a55-44be-84d4-a290f738ac7b | city=Hamburg | price=5000-20000 | sort=price_desc
- Q34: q=- | category=86dbd8d2-0148-4977-ac01-8dbd947024b4 | city=Ankara | price=20000-50000 | sort=newest
- Q35: q=daire | category=775bdf32-9df4-4f2a-b15f-8801f5c775f8 | city=Istanbul | price=50000-100000 | sort=price_asc
- Q36: q=- | category=bee9684b-5047-47f2-8499-7891f80c25e5 | city=Izmir | price=0-1000 | sort=price_desc
- Q37: q=bmw | category=835ca551-6fe0-463b-9634-4181d6feccd4 | city=Cologne | price=1000-5000 | sort=newest
- Q38: q=- | category=93ae26a7-fdd9-43ba-8143-60cbe5d5b44e | city=Frankfurt | price=5000-20000 | sort=price_asc
- Q39: q=ford | category=0a36ca7c-be80-4c1f-b2b9-6c4e29b12f67 | city=Stuttgart | price=20000-50000 | sort=price_desc
- Q40: q=- | category=81cb06c4-96c5-40cf-9343-1f0eed9756c8 | city=Dusseldorf | price=50000-100000 | sort=newest
- Q41: q=araba | category=1debb8f9-cb41-47bf-8e6a-4fcc0423b9ec | city=Berlin | price=0-1000 | sort=price_asc
- Q42: q=- | category=cfcae39a-0287-471c-8944-8f4eab81fd24 | city=Munich | price=1000-5000 | sort=price_desc
- Q43: q=kiralik | category=1922d021-2a55-44be-84d4-a290f738ac7b | city=Hamburg | price=5000-20000 | sort=newest
- Q44: q=- | category=86dbd8d2-0148-4977-ac01-8dbd947024b4 | city=Ankara | price=20000-50000 | sort=price_asc
- Q45: q=daire | category=775bdf32-9df4-4f2a-b15f-8801f5c775f8 | city=Istanbul | price=50000-100000 | sort=price_desc
- Q46: q=- | category=bee9684b-5047-47f2-8499-7891f80c25e5 | city=Izmir | price=0-1000 | sort=newest
- Q47: q=bmw | category=835ca551-6fe0-463b-9634-4181d6feccd4 | city=Cologne | price=1000-5000 | sort=price_asc
- Q48: q=- | category=93ae26a7-fdd9-43ba-8143-60cbe5d5b44e | city=Frankfurt | price=5000-20000 | sort=price_desc
- Q49: q=ford | category=0a36ca7c-be80-4c1f-b2b9-6c4e29b12f67 | city=Stuttgart | price=20000-50000 | sort=newest
- Q50: q=- | category=81cb06c4-96c5-40cf-9343-1f0eed9756c8 | city=Dusseldorf | price=50000-100000 | sort=price_asc

## Parity Results
| Query | Mongo Count | SQL Count | Top20 Overlap % |
| --- | --- | --- | --- |
| Q01 | 0 | 0 | 0.0 |
| Q02 | 0 | 0 | 0.0 |
| Q03 | 0 | 0 | 0.0 |
| Q04 | 0 | 0 | 0.0 |
| Q05 | 0 | 0 | 0.0 |
| Q06 | 0 | 0 | 0.0 |
| Q07 | 0 | 0 | 0.0 |
| Q08 | 0 | 0 | 0.0 |
| Q09 | 0 | 0 | 0.0 |
| Q10 | 0 | 0 | 0.0 |
| Q11 | 0 | 0 | 0.0 |
| Q12 | 0 | 0 | 0.0 |
| Q13 | 0 | 0 | 0.0 |
| Q14 | 0 | 0 | 0.0 |
| Q15 | 0 | 0 | 0.0 |
| Q16 | 0 | 0 | 0.0 |
| Q17 | 0 | 0 | 0.0 |
| Q18 | 0 | 0 | 0.0 |
| Q19 | 0 | 0 | 0.0 |
| Q20 | 0 | 0 | 0.0 |
| Q21 | 0 | 0 | 0.0 |
| Q22 | 0 | 0 | 0.0 |
| Q23 | 0 | 0 | 0.0 |
| Q24 | 0 | 0 | 0.0 |
| Q25 | 0 | 0 | 0.0 |
| Q26 | 0 | 0 | 0.0 |
| Q27 | 0 | 0 | 0.0 |
| Q28 | 0 | 0 | 0.0 |
| Q29 | 0 | 0 | 0.0 |
| Q30 | 0 | 0 | 0.0 |
| Q31 | 0 | 0 | 0.0 |
| Q32 | 0 | 0 | 0.0 |
| Q33 | 0 | 0 | 0.0 |
| Q34 | 0 | 0 | 0.0 |
| Q35 | 0 | 0 | 0.0 |
| Q36 | 0 | 0 | 0.0 |
| Q37 | 0 | 0 | 0.0 |
| Q38 | 0 | 0 | 0.0 |
| Q39 | 0 | 0 | 0.0 |
| Q40 | 0 | 0 | 0.0 |
| Q41 | 0 | 0 | 0.0 |
| Q42 | 0 | 0 | 0.0 |
| Q43 | 0 | 0 | 0.0 |
| Q44 | 0 | 0 | 0.0 |
| Q45 | 0 | 0 | 0.0 |
| Q46 | 0 | 0 | 0.0 |
| Q47 | 0 | 0 | 0.0 |
| Q48 | 0 | 0 | 0.0 |
| Q49 | 0 | 0 | 0.0 |
| Q50 | 0 | 0 | 0.0 |

> Not: Preview ortamında listing datası bulunmadığı için tüm sonuçlar 0 döndü.