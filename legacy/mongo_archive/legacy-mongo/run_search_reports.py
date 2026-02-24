import argparse
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import psycopg2
from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / '.env')
load_dotenv(ROOT_DIR / '.env.local', override=False)

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
DATABASE_URL = os.environ.get('DATABASE_URL')
SLOW_QUERY_THRESHOLD_MS = int(os.environ.get('SLOW_QUERY_THRESHOLD_MS', '800'))

if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL missing for search reports')

mongo_client = MongoClient(MONGO_URL) if MONGO_URL and DB_NAME else None
mongo_db = mongo_client[DB_NAME] if mongo_client and DB_NAME else None
sql_conn = psycopg2.connect(DATABASE_URL)

fallback_cities = ["Berlin", "Munich", "Hamburg", "Ankara", "Istanbul", "Izmir", "Cologne", "Frankfurt", "Stuttgart", "Dusseldorf"]
keywords = ["araba", "ev", "kiralik", "satilik", "daire", "villa", "bmw", "audi", "ford", "mercedes"]
price_ranges = [(0, 1000), (1000, 5000), (5000, 20000), (20000, 50000), (50000, 100000)]
sorts = ["newest", "price_asc", "price_desc"]


def _fetch_sql_categories(limit=10):
    with sql_conn.cursor() as cur:
        cur.execute('SELECT id FROM categories LIMIT %s', (limit,))
        rows = cur.fetchall()
    return [str(row[0]) for row in rows]


def _mongo_search(query):
    if mongo_db is None:
        return 0, []
    filters = {"status": "active"}
    if query.get('category_id'):
        filters['category_id'] = query['category_id']
    if query.get('city'):
        filters['city'] = {"$regex": query['city'], "$options": "i"}
    if query.get('q'):
        filters['$or'] = [
            {"title": {"$regex": query['q'], "$options": "i"}},
            {"description": {"$regex": query['q'], "$options": "i"}},
        ]
    price_filters = []
    if query.get('price_min') is not None:
        price_filters.append({"price.amount": {"$gte": query['price_min']}})
        price_filters.append({"price": {"$gte": query['price_min']}})
    if query.get('price_max') is not None:
        price_filters.append({"price.amount": {"$lte": query['price_max']}})
        price_filters.append({"price": {"$lte": query['price_max']}})
    if price_filters:
        filters['$and'] = filters.get('$and', []) + [{"$or": price_filters}]

    sort_field = 'created_at'
    if query.get('sort') == 'price_asc':
        sort_field = 'price.amount'
    elif query.get('sort') == 'price_desc':
        sort_field = 'price.amount'
    sort_dir = 1 if query.get('sort') == 'price_asc' else -1
    cursor = mongo_db.listings.find(filters, {"id": 1}).sort(sort_field, sort_dir).limit(20)
    ids = [str(doc.get('id') or doc.get('_id')) for doc in cursor]
    count = mongo_db.listings.count_documents(filters)
    return count, ids


def _sql_search(query):
    conditions = ["status = 'active'"]
    params = []
    if query.get('category_id'):
        conditions.append('category_id = %s')
        params.append(query['category_id'])
    if query.get('city'):
        conditions.append('city ILIKE %s')
        params.append(f"%{query['city']}%")
    if query.get('price_min') is not None:
        conditions.append('price_amount >= %s')
        params.append(query['price_min'])
    if query.get('price_max') is not None:
        conditions.append('price_amount <= %s')
        params.append(query['price_max'])
    if query.get('price_min') is not None or query.get('price_max') is not None:
        conditions.append("(price_type = 'FIXED' OR price_type IS NULL)")
    if query.get('q'):
        conditions.append("(tsv_tr @@ plainto_tsquery('turkish', %s) OR tsv_de @@ plainto_tsquery('german', %s) OR title ILIKE %s OR description ILIKE %s)")
        params.extend([query['q'], query['q'], f"%{query['q']}%", f"%{query['q']}%"])

    where_clause = ' AND '.join(conditions) if conditions else 'TRUE'
    order_clause = 'published_at DESC NULLS LAST'
    if query.get('sort') == 'price_asc':
        order_clause = 'price_amount ASC NULLS LAST'
    elif query.get('sort') == 'price_desc':
        order_clause = 'price_amount DESC NULLS LAST'

    with sql_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM listings_search WHERE {where_clause}", params)
        count = cur.fetchone()[0]
        cur.execute(
            f"SELECT listing_id FROM listings_search WHERE {where_clause} ORDER BY {order_clause} LIMIT 20",
            params,
        )
        ids = [str(row[0]) for row in cur.fetchall()]
    return count, ids


def _percentile(values, pct):
    if not values:
        return None
    values_sorted = sorted(values)
    idx = int((pct / 100) * (len(values_sorted) - 1))
    return values_sorted[idx]


def _append_section(path: Path, section: str) -> None:
    if path.exists():
        content = path.read_text().rstrip() + "\n\n" + section.strip() + "\n"
    else:
        content = section.strip() + "\n"
    path.write_text(content)


def run_parity(stage_label: str, queries):
    report_rows = []
    for query in queries:
        mongo_count, mongo_ids = _mongo_search(query)
        sql_count, sql_ids = _sql_search(query)
        overlap = len(set(mongo_ids) & set(sql_ids))
        ratio = round((overlap / 20) * 100, 2) if mongo_ids and sql_ids else 0.0
        report_rows.append({
            **query,
            "mongo_count": mongo_count,
            "sql_count": sql_count,
            "top20_overlap_pct": ratio,
            "mongo_ids": mongo_ids,
            "sql_ids": sql_ids,
        })

    mongo_total = mongo_db.listings.count_documents({}) if mongo_db is not None else 0
    sql_total = _sql_search({"q": None})[0]

    lines = [
        f"## Stage {stage_label}",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        f"Mongo listing count: {mongo_total}",
        f"Postgres listings_search count: {sql_total}",
        "",
        "### Golden Query Set (50)",
    ]
    for row in report_rows:
        lines.append(
            f"- {row['id']}: q={row['q'] or '-'} | category={row['category_id'] or '-'} | city={row['city'] or '-'} | price={row['price_min']}-{row['price_max']} | sort={row['sort']}"
        )

    lines.append("\n### Parity Results")
    lines.append("| Query | Mongo Count | SQL Count | Top20 Overlap % |")
    lines.append("| --- | --- | --- | --- |")
    for row in report_rows:
        lines.append(
            f"| {row['id']} | {row['mongo_count']} | {row['sql_count']} | {row['top20_overlap_pct']} |"
        )

    _append_section(Path('/app/memory/SEARCH_PARITY_REPORT.md'), "\n".join(lines))

    raw_lines = [
        f"## Stage {stage_label}",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        "",
    ]
    for row in report_rows:
        raw_lines.append(f"### {row['id']}")
        raw_lines.append(f"- Params: q={row['q'] or '-'} | category={row['category_id'] or '-'} | city={row['city'] or '-'} | price={row['price_min']}-{row['price_max']} | sort={row['sort']}")
        raw_lines.append(f"- Mongo IDs (top20): {', '.join(row['mongo_ids']) if row['mongo_ids'] else '[]'}")
        raw_lines.append(f"- SQL IDs (top20): {', '.join(row['sql_ids']) if row['sql_ids'] else '[]'}")
        raw_lines.append("")

    _append_section(Path('/app/memory/SEARCH_PARITY_RAW.md'), "\n".join(raw_lines))


def run_benchmark(stage_label: str, queries):
    import time

    def build_sql(query):
        conditions = ["status = 'active'"]
        params = []
        if query.get('price_min') is not None:
            conditions.append('price_amount >= %s')
            params.append(query['price_min'])
        if query.get('price_max') is not None:
            conditions.append('price_amount <= %s')
            params.append(query['price_max'])
        if query.get('price_min') is not None or query.get('price_max') is not None:
            conditions.append("(price_type = 'FIXED' OR price_type IS NULL)")
        if query.get('q'):
            conditions.append("(tsv_tr @@ plainto_tsquery('turkish', %s) OR tsv_de @@ plainto_tsquery('german', %s) OR title ILIKE %s OR description ILIKE %s)")
            params.extend([query['q'], query['q'], f"%{query['q']}%", f"%{query['q']}%"])
        where_clause = ' AND '.join(conditions) if conditions else 'TRUE'
        order_clause = 'published_at DESC NULLS LAST'
        if query.get('sort') == 'price_asc':
            order_clause = 'price_amount ASC NULLS LAST'
        elif query.get('sort') == 'price_desc':
            order_clause = 'price_amount DESC NULLS LAST'
        sql = f"SELECT listing_id FROM listings_search WHERE {where_clause} ORDER BY {order_clause} LIMIT 20"
        return sql, params

    def run_query(conn, sql, params):
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cur.fetchall()
        return (time.perf_counter() - start) * 1000

    cold_latencies = []
    for query in queries:
        sql, params = build_sql(query)
        conn = psycopg2.connect(DATABASE_URL)
        latency = run_query(conn, sql, params)
        conn.close()
        cold_latencies.append(latency)

    warm_latencies = []
    conn = psycopg2.connect(DATABASE_URL)
    for query in queries:
        sql, params = build_sql(query)
        latency = run_query(conn, sql, params)
        warm_latencies.append(latency)
    conn.close()

    cold_p50 = _percentile(cold_latencies, 50)
    cold_p95 = _percentile(cold_latencies, 95)
    cold_max = max(cold_latencies) if cold_latencies else None
    warm_p50 = _percentile(warm_latencies, 50)
    warm_p95 = _percentile(warm_latencies, 95)
    warm_max = max(warm_latencies) if warm_latencies else None

    lines = [
        f"## Stage {stage_label}",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        "",
        "### Summary",
        f"- Cold cache p50: {round(cold_p50, 2) if cold_p50 is not None else 'n/a'} ms",
        f"- Cold cache p95: {round(cold_p95, 2) if cold_p95 is not None else 'n/a'} ms",
        f"- Cold cache max: {round(cold_max, 2) if cold_max is not None else 'n/a'} ms",
        f"- Warm cache p50: {round(warm_p50, 2) if warm_p50 is not None else 'n/a'} ms",
        f"- Warm cache p95: {round(warm_p95, 2) if warm_p95 is not None else 'n/a'} ms",
        f"- Warm cache max: {round(warm_max, 2) if warm_max is not None else 'n/a'} ms",
        "",
        "### Query Latencies",
        "| Query | Cold (ms) | Warm (ms) |",
        "| --- | --- | --- |",
    ]
    for idx, query in enumerate(queries):
        lines.append(
            f"| {query['id']} | {round(cold_latencies[idx], 2)} | {round(warm_latencies[idx], 2)} |"
        )

    _append_section(Path('/app/memory/SEARCH_BENCHMARK_REPORT.md'), "\n".join(lines))

    slow_lines = [
        f"## Stage {stage_label}",
        f"Threshold: > {SLOW_QUERY_THRESHOLD_MS} ms",
    ]
    slow_found = False
    for idx, query in enumerate(queries):
        cold = cold_latencies[idx]
        warm = warm_latencies[idx]
        if cold > SLOW_QUERY_THRESHOLD_MS or warm > SLOW_QUERY_THRESHOLD_MS:
            slow_found = True
            slow_lines.append(
                f"- {query['id']}: cold={round(cold, 2)}ms, warm={round(warm, 2)}ms | q={query['q'] or '-'} | sort={query['sort']} | price={query['price_min']}-{query['price_max']}"
            )
    if not slow_found:
        slow_lines.append("- Slow query bulunmadı.")

    _append_section(Path('/app/memory/SEARCH_SLOW_QUERIES.md'), "\n".join(slow_lines))

    explain_lines = [f"## Stage {stage_label}", f"Generated at: {datetime.utcnow().isoformat()}Z"]
    conn = psycopg2.connect(DATABASE_URL)
    for query in queries[:3]:
        sql, params = build_sql(query)
        explain_lines.append(f"\n### {query['id']}")
        with conn.cursor() as cur:
            cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + sql, params)
            rows = cur.fetchall()
        explain_lines.extend([row[0] for row in rows])
    conn.close()

    _append_section(Path('/app/memory/SEARCH_EXPLAIN_ANALYZE_RAW.md'), "\n".join(explain_lines))


def main():
    parser = argparse.ArgumentParser(description='Run search parity/benchmark reports')
    parser.add_argument('--stage', required=True)
    args = parser.parse_args()

    categories = _fetch_sql_categories(10)
    queries = []
    for i in range(50):
        category_id = categories[i % len(categories)] if categories else None
        city = fallback_cities[i % len(fallback_cities)]
        keyword = keywords[i % len(keywords)] if i % 2 == 0 else None
        price_min, price_max = price_ranges[i % len(price_ranges)]
        sort = sorts[i % len(sorts)]
        queries.append({
            "id": f"Q{i+1:02d}",
            "category_id": category_id,
            "city": city,
            "q": keyword,
            "price_min": price_min,
            "price_max": price_max,
            "sort": sort,
        })

    benchmark_queries = [
        {
            "id": f"B{i+1:02d}",
            "q": keywords[i % len(keywords)] if i % 2 == 0 else None,
            "price_min": price_ranges[i % len(price_ranges)][0],
            "price_max": price_ranges[i % len(price_ranges)][1],
            "sort": sorts[i % len(sorts)],
        }
        for i in range(10)
    ]

    run_parity(args.stage, queries)
    run_benchmark(args.stage, benchmark_queries)


if __name__ == '__main__':
    main()
