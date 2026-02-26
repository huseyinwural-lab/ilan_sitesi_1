#!/usr/bin/env python3
"""
Bulk reindex script for Meilisearch projection.

Usage:
  python /app/backend/scripts/reindex_meili_projection.py --chunk-size 250 --reset-index
  python /app/backend/scripts/reindex_meili_projection.py --chunk-size 200 --max-docs 1000
"""

import argparse
import asyncio
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.services.meilisearch_index import (
    bulk_reindex_search_projection,
    get_active_meili_runtime,
    meili_clear_documents,
)


async def run(chunk_size: int, max_docs: int | None, reset_index: bool) -> None:
    started = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        runtime = await get_active_meili_runtime(session)
        if reset_index:
            await meili_clear_documents(runtime)

        count, elapsed = await bulk_reindex_search_projection(
            session=session,
            chunk_size=chunk_size,
            max_docs=max_docs,
        )

    ended = datetime.now(timezone.utc)
    print("[MEILI_REINDEX] status=done")
    print(f"[MEILI_REINDEX] index_name={runtime['index_name']} url={runtime['url']}")
    print(f"[MEILI_REINDEX] docs_indexed={count} chunk_size={chunk_size} max_docs={max_docs}")
    print(f"[MEILI_REINDEX] elapsed_seconds={elapsed:.3f}")
    print(f"[MEILI_REINDEX] started_at={started.isoformat()} ended_at={ended.isoformat()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk reindex listing projection into Meilisearch")
    parser.add_argument("--chunk-size", type=int, default=200)
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument("--reset-index", action="store_true")
    args = parser.parse_args()

    chunk_size = min(1000, max(25, args.chunk_size))
    max_docs = args.max_docs if args.max_docs and args.max_docs > 0 else None
    asyncio.run(run(chunk_size=chunk_size, max_docs=max_docs, reset_index=args.reset_index))


if __name__ == "__main__":
    main()
