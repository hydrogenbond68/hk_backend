"""set_image.py — Set image_urls on ONE product.
Usage:
    python set_image.py 12 https://a.jpg https://b.jpg
    python set_image.py 12 --clear
"""
import sys, json, traceback

def find_db(app):
    ext = app.extensions.get("sqlalchemy")
    if ext is not None and hasattr(ext, "create_all"):
        return ext
    for p in ("app.extensions", "app.database", "app.db"):
        try:
            m = __import__(p, fromlist=["db"]); d = getattr(m, "db", None)
            if d: return d
        except ImportError: pass
    return None

def find_product_class():
    for p in ("app.models", "app.models.product", "app.models.products", "models"):
        try:
            m = __import__(p, fromlist=["Product"]); k = getattr(m, "Product", None)
            if k: return k
        except ImportError: pass
    return None

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)

    pid = int(sys.argv[1])
    rest = sys.argv[2:]
    if rest == ["--clear"]:
        new_urls = []
    else:
        new_urls = [u for u in rest if u.startswith(("http://", "https://", "/"))]
        if not new_urls:
            print("FAIL: no valid URLs given"); sys.exit(2)

    from app import create_app
    app = create_app()
    db = find_db(app)
    Product = find_product_class()
    if not db or not Product:
        print("FAIL: db or Product not found"); sys.exit(3)

    col = Product.__table__.columns.get("image_urls")
    is_json = "json" in type(col.type).__name__.lower()

    with app.app_context():
        p = db.session.get(Product, pid)
        if not p:
            print(f"FAIL: no product with id={pid}"); sys.exit(4)
        p.image_urls = new_urls if is_json else json.dumps(new_urls)
        db.session.commit()
        print(f"✅ product {pid} ({p.name[:50]}) → {len(new_urls)} image(s)")
        for u in new_urls:
            print(f"   {u}")

if __name__ == "__main__":
    try: main()
    except Exception:
        traceback.print_exc(); sys.exit(1)
