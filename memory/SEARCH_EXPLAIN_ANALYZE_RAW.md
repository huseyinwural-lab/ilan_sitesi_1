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

## Stage 0.5
Generated at: 2026-02-23T13:46:42.700004Z

### B01
Limit  (cost=448.14..448.19 rows=20 width=24) (actual time=1.497..1.501 rows=16 loops=1)
  Buffers: shared hit=145
  ->  Sort  (cost=448.14..448.24 rows=39 width=24) (actual time=1.495..1.496 rows=16 loops=1)
        Sort Key: published_at DESC NULLS LAST
        Sort Method: quicksort  Memory: 26kB
        Buffers: shared hit=145
        ->  Bitmap Heap Scan on listings_search  (cost=194.25..447.11 rows=39 width=24) (actual time=0.874..1.453 rows=16 loops=1)
              Recheck Cond: ((price_amount >= '0'::numeric) AND (price_amount <= '1000'::numeric))
              Filter: ((((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((status)::text = 'active'::text) AND ((tsv_tr @@ '''arap'''::tsquery) OR (tsv_de @@ '''araba'''::tsquery) OR ((title)::text ~~* '%araba%'::text) OR (description ~~* '%araba%'::text)))
              Rows Removed by Filter: 106
              Heap Blocks: exact=107
              Buffers: shared hit=142
              ->  Bitmap Index Scan on ix_listings_search_category_price  (cost=0.00..194.24 rows=123 width=0) (actual time=0.818..0.819 rows=122 loops=1)
                    Index Cond: ((price_amount >= '0'::numeric) AND (price_amount <= '1000'::numeric))
                    Buffers: shared hit=35
Planning:
  Buffers: shared hit=453
Planning Time: 3.063 ms
Execution Time: 1.709 ms

### B02
Limit  (cost=477.22..477.27 rows=20 width=22) (actual time=4.832..4.839 rows=20 loops=1)
  Buffers: shared hit=360
  ->  Sort  (cost=477.22..479.13 rows=763 width=22) (actual time=4.828..4.832 rows=20 loops=1)
        Sort Key: price_amount
        Sort Method: top-N heapsort  Memory: 27kB
        Buffers: shared hit=360
        ->  Seq Scan on listings_search  (cost=0.00..456.92 rows=763 width=22) (actual time=0.036..4.595 rows=749 loops=1)
              Filter: ((price_amount >= '1000'::numeric) AND (price_amount <= '5000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((status)::text = 'active'::text))
              Rows Removed by Filter: 4251
              Buffers: shared hit=357
Planning:
  Buffers: shared hit=6
Planning Time: 0.300 ms
Execution Time: 4.872 ms

### B03
Limit  (cost=515.37..515.42 rows=20 width=22) (actual time=3.910..3.916 rows=20 loops=1)
  Buffers: shared hit=357
  ->  Sort  (cost=515.37..516.17 rows=319 width=22) (actual time=3.907..3.909 rows=20 loops=1)
        Sort Key: price_amount DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 27kB
        Buffers: shared hit=357
        ->  Seq Scan on listings_search  (cost=0.00..506.88 rows=319 width=22) (actual time=0.016..3.867 rows=90 loops=1)
              Filter: ((price_amount >= '5000'::numeric) AND (price_amount <= '20000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((status)::text = 'active'::text) AND ((tsv_tr @@ '''kiralik'''::tsquery) OR (tsv_de @@ '''kiral'''::tsquery) OR ((title)::text ~~* '%kiralik%'::text) OR (description ~~* '%kiralik%'::text)))
              Rows Removed by Filter: 4910
              Buffers: shared hit=357
Planning:
  Buffers: shared hit=6
Planning Time: 0.399 ms
Execution Time: 3.943 ms

## Stage 1.0
Generated at: 2026-02-23T13:48:28.202421Z

### B01
Limit  (cost=448.14..448.19 rows=20 width=24) (actual time=1.588..1.592 rows=16 loops=1)
  Buffers: shared hit=145
  ->  Sort  (cost=448.14..448.24 rows=39 width=24) (actual time=1.586..1.587 rows=16 loops=1)
        Sort Key: published_at DESC NULLS LAST
        Sort Method: quicksort  Memory: 26kB
        Buffers: shared hit=145
        ->  Bitmap Heap Scan on listings_search  (cost=194.25..447.11 rows=39 width=24) (actual time=0.969..1.520 rows=16 loops=1)
              Recheck Cond: ((price_amount >= '0'::numeric) AND (price_amount <= '1000'::numeric))
              Filter: ((((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((status)::text = 'active'::text) AND ((tsv_tr @@ '''arap'''::tsquery) OR (tsv_de @@ '''araba'''::tsquery) OR ((title)::text ~~* '%araba%'::text) OR (description ~~* '%araba%'::text)))
              Rows Removed by Filter: 106
              Heap Blocks: exact=107
              Buffers: shared hit=142
              ->  Bitmap Index Scan on ix_listings_search_category_price  (cost=0.00..194.24 rows=123 width=0) (actual time=0.912..0.912 rows=122 loops=1)
                    Index Cond: ((price_amount >= '0'::numeric) AND (price_amount <= '1000'::numeric))
                    Buffers: shared hit=35
Planning:
  Buffers: shared hit=453
Planning Time: 6.047 ms
Execution Time: 1.686 ms

### B02
Limit  (cost=477.22..477.27 rows=20 width=22) (actual time=4.648..4.653 rows=20 loops=1)
  Buffers: shared hit=360
  ->  Sort  (cost=477.22..479.13 rows=763 width=22) (actual time=4.645..4.647 rows=20 loops=1)
        Sort Key: price_amount
        Sort Method: top-N heapsort  Memory: 27kB
        Buffers: shared hit=360
        ->  Seq Scan on listings_search  (cost=0.00..456.92 rows=763 width=22) (actual time=0.040..4.428 rows=749 loops=1)
              Filter: ((price_amount >= '1000'::numeric) AND (price_amount <= '5000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((status)::text = 'active'::text))
              Rows Removed by Filter: 4251
              Buffers: shared hit=357
Planning:
  Buffers: shared hit=6
Planning Time: 0.283 ms
Execution Time: 4.683 ms

### B03
Limit  (cost=515.37..515.42 rows=20 width=22) (actual time=3.638..3.643 rows=20 loops=1)
  Buffers: shared hit=357
  ->  Sort  (cost=515.37..516.17 rows=319 width=22) (actual time=3.635..3.637 rows=20 loops=1)
        Sort Key: price_amount DESC NULLS LAST
        Sort Method: top-N heapsort  Memory: 27kB
        Buffers: shared hit=357
        ->  Seq Scan on listings_search  (cost=0.00..506.88 rows=319 width=22) (actual time=0.019..3.596 rows=90 loops=1)
              Filter: ((price_amount >= '5000'::numeric) AND (price_amount <= '20000'::numeric) AND (((price_type)::text = 'FIXED'::text) OR (price_type IS NULL)) AND ((status)::text = 'active'::text) AND ((tsv_tr @@ '''kiralik'''::tsquery) OR (tsv_de @@ '''kiral'''::tsquery) OR ((title)::text ~~* '%kiralik%'::text) OR (description ~~* '%kiralik%'::text)))
              Rows Removed by Filter: 4910
              Buffers: shared hit=357
Planning:
  Buffers: shared hit=6
Planning Time: 0.422 ms
Execution Time: 3.679 ms
