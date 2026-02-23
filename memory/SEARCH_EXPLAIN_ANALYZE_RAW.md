# EXPLAIN ANALYZE RAW OUTPUTS

## B01

Limit  (cost=8.19..8.19 rows=1 width=24) (actual time=0.041..0.042 rows=0 loops=1)
  Buffers: shared hit=5
  ->  Sort  (cost=8.19..8.19 rows=1 width=24) (actual time=0.039..0.040 rows=0 loops=1)
        Sort Key: published_at DESC NULLS LAST
        Sort Method: quicksort  Memory: 25kB
        Buffers: shared hit=5
        ->  Index Scan using ix_listings_search_core on listings_search  (cost=0.14..8.18 rows=1 width=24) (actual time=0.004..0.004 rows=0 loops=1)
              Index Cond: ((status)::text = 'active'::text)
              Filter: ((price_amount >= '0'::numeric) AND (price_amount <= '1000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((tsv_tr @@ '''arap'''::tsquery) OR (tsv_de @@ '''araba'''::tsquery) OR ((title)::text ~~* '%araba%'::text) OR (description ~~* '%araba%'::text)))
              Buffers: shared hit=2
Planning:
  Buffers: shared hit=465
Planning Time: 3.651 ms
Execution Time: 0.107 ms

## B02

Limit  (cost=8.18..8.18 rows=1 width=32) (actual time=0.021..0.022 rows=0 loops=1)
  Buffers: shared hit=5
  ->  Sort  (cost=8.18..8.18 rows=1 width=32) (actual time=0.020..0.020 rows=0 loops=1)
        Sort Key: price_amount
        Sort Method: quicksort  Memory: 25kB
        Buffers: shared hit=5
        ->  Index Scan using ix_listings_search_core on listings_search  (cost=0.14..8.17 rows=1 width=32) (actual time=0.002..0.003 rows=0 loops=1)
              Index Cond: ((status)::text = 'active'::text)
              Filter: ((price_amount >= '1000'::numeric) AND (price_amount <= '5000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)))
              Buffers: shared hit=2
Planning:
  Buffers: shared hit=25
Planning Time: 0.238 ms
Execution Time: 0.040 ms

## B03

Limit  (cost=8.19..8.19 rows=1 width=32) (actual time=0.011..0.012 rows=0 loops=1)
  Buffers: shared hit=2
  ->  Sort  (cost=8.19..8.19 rows=1 width=32) (actual time=0.009..0.010 rows=0 loops=1)
        Sort Key: price_amount DESC NULLS LAST
        Sort Method: quicksort  Memory: 25kB
        Buffers: shared hit=2
        ->  Index Scan using ix_listings_search_core on listings_search  (cost=0.14..8.18 rows=1 width=32) (actual time=0.003..0.004 rows=0 loops=1)
              Index Cond: ((status)::text = 'active'::text)
              Filter: ((price_amount >= '5000'::numeric) AND (price_amount <= '20000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((tsv_tr @@ '''kiralik'''::tsquery) OR (tsv_de @@ '''kiral'''::tsquery) OR ((title)::text ~~* '%kiralik%'::text) OR (description ~~* '%kiralik%'::text)))
              Buffers: shared hit=2
Planning:
  Buffers: shared hit=21
Planning Time: 0.342 ms
Execution Time: 0.033 ms