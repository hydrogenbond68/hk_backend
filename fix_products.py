"""
fix_products.py - Option 1 fix: force model imports, then create tables.
Run from project root with virtualenv active:  python fix_products.py
"""

import sys
import traceback

MODEL_MODULES = [
    "app.models",
    "app.models.product",
    "app.models.products",
    "models",
]
DB_MODULES = [
    "app.extensions",
    "app.database",
    "app.db",
    "extensions",
    "database",
]


def banner(msg):
    print("\n" + "=" * 64)
    print(f"  {msg}")
    print("=" * 64)


def main():
    banner("STEP 1 - Loading Flask app via create_app()")
    try:
        from app import create_app
        app = create_app()
        print("OK: app = create_app()")
    except Exception:
        print("FAIL: could not load create_app(). Traceback:")
        traceback.print_exc()
        sys.exit(1)

    banner("STEP 2 - Locating the db instance")
    db = None
    db_source = None
    ext = app.extensions.get("sqlalchemy")
    if ext is not None and hasattr(ext, "create_all"):
        db, db_source = ext, "app.extensions['sqlalchemy']"
    else:
        for path in DB_MODULES:
            try:
                mod = __import__(path, fromlist=["db"])
                candidate = getattr(mod, "db", None)
                if candidate and hasattr(candidate, "create_all"):
                    db, db_source = candidate, path
                    break
            except ImportError:
                continue

    if db is None:
        print("FAIL: could not find the db instance.")
        print("Edit DB_MODULES in this script to match your project.")
        sys.exit(2)
    print(f"OK: db located via: {db_source}")

    banner("STEP 3 - Showing configured database URI")
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "<not set>")
    print(f"SQLALCHEMY_DATABASE_URI = {uri}")

    with app.app_context():
        banner("STEP 4 - KEY FIX: force-import all model modules")
        imported = []
        for path in MODEL_MODULES:
            try:
                __import__(path)
                imported.append(path)
                print(f"OK: imported: {path}")
            except ImportError:
                print(f".. skipped: {path} (not found)")

        if not imported:
            print("FAIL: no model module imported. Edit MODEL_MODULES.")
            sys.exit(3)

        banner("STEP 5 - Metadata AFTER importing models")
        registered = sorted(db.metadata.tables.keys())
        print(f"Registered tables ({len(registered)}): {registered}")

        if "products" not in registered:
            print("FAIL: 'products' not in metadata.")
            print("Confirm the file defining `class Product(db.Model)` is")
            print("covered by one of MODEL_MODULES at the top of this script.")
            sys.exit(4)

        banner("STEP 6 - Calling db.create_all()")
        db.create_all()
        print("OK: db.create_all() finished")

        banner("STEP 7 - Verifying with a real SELECT")
        from sqlalchemy import inspect, text
        tables = inspect(db.engine).get_table_names()
        print(f"Tables in DB ({len(tables)}): {tables}")

        if "products" not in tables:
            print("FAIL: 'products' still missing after create_all().")
            print("Your Product model is bound to a DIFFERENT db instance.")
            sys.exit(5)

        row = db.session.execute(text(
            "SELECT COUNT(*) FROM products "
            "WHERE is_active = 1 AND is_featured = 1"
        )).scalar()
        print(f"OK: SELECT on products succeeded - {row} featured+active row(s)")

        banner("SUCCESS")
        print("'products' table exists and the failing query now works.")
        print("Restart your server:  python run.py")
        print("")
        print("PERMANENT FIX - add to app/__init__.py inside create_app():")
        print("    from app.models import Product")
        print("    with app.app_context():")
        print("        db.create_all()")


if __name__ == "__main__":
    main()
