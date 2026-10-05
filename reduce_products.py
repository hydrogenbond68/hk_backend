#!/usr/bin/env python3
"""
Reduce the products catalog from its current size to a target count
(default 100), keeping a selection determined by a chosen strategy.

SAFE BY DEFAULT
  * Dry-run: prints what would be deleted; changes nothing.
      python reduce_products.py --strategy recent
  * To apply: add --execute (backs up the DB first).
      python reduce_products.py --strategy recent --execute
  * Refuses to run if it cannot prove exactly (current - target) rows would
    be removed, and aborts if the keep-set is smaller than the target.

STRATEGIES
  recent           Keep the N most recently created products.
  random           Keep a random sample of N.
  featured         Keep all featured products, then fill to N with the
                   most recent non-featured ones.
  popularity       Keep the N products with the most reviews/ratings. When the
                   reviews table is empty (as it is on a fresh DB), falls back
                   to high stock + featured as a popularity proxy.
  category         Balance the N products across categories proportionally.
  inactive-first   (informational) show which products would be removed
                   because they are inactive, regardless of N.
"""
import argparse
import os
import random
import shutil
import sqlite3
import sys
from collections import defaultdict

DB_DEFAULT = "instance/harykims.db"


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def current_count(conn):
    return conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


def has_reviews(conn):
    try:
        return conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] > 0
    except sqlite3.OperationalError:
        return False


# --- strategies --------------------------------------------------------------

def strategy_recent(conn, target):
    rows = conn.execute(
        "SELECT id FROM products ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return set(r["id"] for r in rows[:target]), []


def strategy_random(conn, target, seed):
    ids = [r["id"] for r in conn.execute("SELECT id FROM products").fetchall()]
    rng = random.Random(seed)
    rng.shuffle(ids)
    return set(ids[:target]), []


def strategy_featured(conn, target):
    keep_ids = set(
        r["id"] for r in conn.execute(
            "SELECT id FROM products WHERE is_featured = 1 ORDER BY created_at DESC"
        ).fetchall()
    )
    # Fill only from active rows. Inactive products are filtered out of every
    # catalog response, so keeping them would leave the storefront showing
    # fewer than `target` products.
    extra = [
        r["id"] for r in conn.execute(
            "SELECT id FROM products WHERE is_featured = 0 AND is_active = 1 "
            "ORDER BY created_at DESC, id DESC"
        ).fetchall()
    ]
    need = target - len(keep_ids)
    keep_ids.update(extra[: max(0, need)])
    return keep_ids, []


def strategy_popularity(conn, target):
    if has_reviews(conn):
        rows = conn.execute(
            """
            SELECT p.id,
                   (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_count,
                   COALESCE((SELECT AVG(r.rating) FROM reviews r WHERE r.product_id = p.id), 0) AS avg_rating
            FROM products p
            ORDER BY review_count DESC, avg_rating DESC, p.created_at DESC
            """
        ).fetchall()
        keep_ids = set(r["id"] for r in rows[:target])
        return keep_ids, []

    # No review data: use featured + high stock as a best-seller proxy.
    rows = conn.execute(
        """
        SELECT id FROM products
        ORDER BY is_featured DESC, stock_quantity DESC, created_at DESC
        """
    ).fetchall()
    return set(r["id"] for r in rows[:target]), [
        "reviews table is empty; popularity proxy uses featured + stock_quantity"
    ]


def strategy_category(conn, target):
    by_cat = defaultdict(list)
    for r in conn.execute(
        "SELECT id, category FROM products ORDER BY created_at DESC"
    ).fetchall():
        by_cat[r["category"]].append(r["id"])

    keep = set()
    # Round-robin so each category gets a fair share, then top-up larger ones.
    ordered = sorted(by_cat.items(), key=lambda kv: -len(kv[1]))
    while len(keep) < target and ordered:
        progressed = False
        for cat, ids in ordered:
            if not ids:
                continue
            keep.add(ids.pop(0))
            progressed = True
            if len(keep) >= target:
                break
        if not progressed:
            break
    # If there were fewer than `target` products total, keep everything.
    return keep, []


def strategy_inactive(conn, target):
    rows = conn.execute(
        "SELECT id, name FROM products WHERE is_active = 0"
    ).fetchall()
    candidates = set(r["id"] for r in rows)
    return set(), rows  # never-delete set is empty -> nothing kept by this strategy


STRATEGIES = {
    "recent": strategy_recent,
    "random": strategy_random,
    "featured": strategy_featured,
    "popularity": strategy_popularity,
    "category": strategy_category,
    "inactive-first": strategy_inactive,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DB_DEFAULT, help="Path to the SQLite DB.")
    ap.add_argument("--target", type=int, default=100, help="Number of products to KEEP.")
    ap.add_argument("--strategy", choices=STRATEGIES, default="recent")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed (random strategy only).")
    ap.add_argument("--show-ids", action="store_true", help="Print the IDs that would be KEPT.")
    ap.add_argument("--execute", action="store_true", help="Write changes (dry-run is default).")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 2

    conn = connect(args.db)
    total = current_count(conn)

    if args.strategy == "inactive-first":
        keep_ids, info = strategy_inactive(conn, args.target)
        remove_ids = [r["id"] for r in conn.execute("SELECT id FROM products").fetchall()]
        print(f"Products: {total} total, {len(info)} inactive.")
        if args.show_ids:
            for r in info:
                print(f"  inactive  id={r['id']:<6} {r['name']}")
        print("Use --strategy inactive-first --execute to mark them is_active=0 instead.")
        conn.close()
        # inactive-first only *reports* by default; --execute would soft-delete.
        if not args.execute:
            return 0
        conn.execute("UPDATE products SET is_active = 0 WHERE is_active = 0")
        conn.commit()
        print(f"Marked {conn.total_changes} inactive products (they were already). Nothing changed.")
        return 0

    keep_ids, notes = STRATEGIES[args.strategy](conn, args.target) if args.strategy != "random" \
        else strategy_random(conn, args.target, args.seed)
    for n in notes:
        print(f"NOTE: {n}")

    if len(keep_ids) > total:
        print(f"Refusing: keep-set ({len(keep_ids)}) exceeds total ({total}).", file=sys.stderr)
        return 2

    remove_ids = [
        r["id"] for r in conn.execute("SELECT id FROM products").fetchall()
        if r["id"] not in keep_ids
    ]

    print(f"Strategy : {args.strategy}")
    print(f"Total    : {total}")
    print(f"Keep     : {len(keep_ids)} (requested {args.target})")
    print(f"Remove   : {len(remove_ids)}")
    if total < args.target:
        print(f"WARNING  : only {total} products exist; {args.target - total} short of target. Nothing deleted.")
        if args.show_ids:
            print("  keeping all:", sorted(keep_ids))
        return 0

    if len(remove_ids) != total - len(keep_ids) or len(keep_ids) != min(args.target, total):
        print("Refusing: arithmetic check failed. Aborting without changes.", file=sys.stderr)
        return 2

    if args.show_ids:
        print("\nKeeping:")
        for i in sorted(keep_ids):
            row = conn.execute("SELECT id, name, category, is_featured FROM products WHERE id=?", (i,)).fetchone()
            print(f"  id={row['id']:<6} feat={int(row['is_featured'])} {row['category'][:18]:<18} {row['name'][:40]}")

    if not args.execute:
        print("\nDRY RUN — no changes written. Re-run with --execute to apply.")
        print("A backup of the DB is created automatically before the first real write.")
        conn.close()
        return 0

    backup = args.db + ".bak"
    shutil.copy2(args.db, backup)
    print(f"\nBackup written to {backup}")
    print("Executing deletion inside a transaction...")

    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "DELETE FROM products WHERE id IN (" + ",".join("?" * len(remove_ids)) + ")",
        remove_ids,
    )
    conn.execute("SELECT COUNT(*) FROM products")  # sanity
    conn.commit()
    after = current_count(conn)
    print(f"Done. products: {total} -> {after}. Deleted {len(remove_ids)}.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
