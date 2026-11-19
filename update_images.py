"""update_images.py — Assign category-appropriate image URLs to every product."""

import sys, traceback

# Curated image URLs per category. Add more to any list for variety.
CATEGORY_IMAGES = {
    "Electronics-Phones": [
        "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&q=80",
        "https://i.pinimg.com/736x/71/3d/d2/713dd21e7bb9496fe2fc1aee5acc8072.jpg",
        "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&q=80",
        "https://i.pinimg.com/736x/78/db/a5/78dba5e24b48ba31fcc08b631d54d43f.jpg",
        "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=800&q=80",
    ],
    "Electronics-Laptops": [
        "https://i.pinimg.com/736x/b0/de/8d/b0de8d57d203d0babc0862ab1b49a0c6.jpg",
        "https://i.pinimg.com/736x/01/64/fa/0164fa00a7c4d6404557b5f54ae190d1.jpg",
        "https://i.pinimg.com/1200x/27/26/2b/27262bc00dfe0f4c789cb45427f868aa.jpg",
        "https://i.pinimg.com/1200x/bf/04/95/bf0495ba6a22d1d11d69b56bda151f2a.jpg",
    ],
    "Electronics-Accessories": [
        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&q=80",
        "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80",
        "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=800&q=80",
    ],
    "Fashion-Men's Clothing": [
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&q=80",
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800&q=80",
        "https://images.unsplash.com/photo-1598808503746-f34c53b9323e?w=800&q=80",
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
    ],
    "Fashion-Women's Clothing": [
        "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800&q=80",
        "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=800&q=80",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&q=80",
        "https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?w=800&q=80",
    ],
    "Home & Kitchen-Cookware": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80",
        "https://images.unsplash.com/photo-1584990347449-39b4a7b4c0b0?w=800&q=80",
        "https://images.unsplash.com/photo-1584346133934-a3afd2a33c4c?w=800&q=80",
    ],
    "Home & Kitchen-Furniture": [
        "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800&q=80",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=80",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&q=80",
        "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800&q=80",
    ],
    "Beauty & Health-Skincare": [
        "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800&q=80",
        "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=800&q=80",
        "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=800&q=80",
    ],
    "Sports & Outdoors-Fitness": [
        "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80",
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80",
        "https://images.unsplash.com/photo-1534258936925-c58bed479fcb?w=800&q=80",
    ],
    "Sports & Outdoors-Outdoor Gear": [
        "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&q=80",
        "https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?w=800&q=80",
        "https://images.unsplash.com/photo-1551632811-561732d1e306?w=800&q=80",
    ],
    "Groceries-Beverages": [
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800&q=80",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&q=80",
        "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=800&q=80",
    ],
    "Groceries-Snacks": [
        "https://images.unsplash.com/photo-1599599810694-b5b37304c041?w=800&q=80",
        "https://images.unsplash.com/photo-1511381939415-e44015466834?w=800&q=80",
        "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=800&q=80",
    ],
}

# Fallback if category key not found
DEFAULT_IMAGES = [
    "https://i.pinimg.com/736x/78/db/a5/78dba5e24b48ba31fcc08b631d54d43f.jpg",
]


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


def find_class(name, modules):
    for p in modules:
        try:
            m = __import__(p, fromlist=[name]); k = getattr(m, name, None)
            if k: return k
        except ImportError: pass
    return None


def main():
    from app import create_app
    app = create_app()
    db = find_db(app)
    if not db:
        print("FAIL: db not found"); sys.exit(1)

    Product = find_class("Product", ("app.models", "app.models.product", "app.models.products", "models"))
    if not Product:
        print("FAIL: Product model not found"); sys.exit(2)

    # Determine how image_urls column behaves (JSON vs TEXT)
    col = Product.__table__.columns.get("image_urls")
    if col is None:
        print("FAIL: Product has no image_urls column"); sys.exit(3)
    is_json = "json" in type(col.type).__name__.lower()
    print(f"image_urls column type: {type(col.type).__name__}  (JSON column: {is_json})")

    import json as _json

    updated = 0
    with app.app_context():
        products = db.session.query(Product).all()
        for p in products:
            key = f"{p.category}-{p.sub_category}"
            urls = CATEGORY_IMAGES.get(key) or DEFAULT_IMAGES
            if is_json:
                p.image_urls = list(urls)
            else:
                p.image_urls = _json.dumps(list(urls))
            updated += 1

        db.session.commit()
        print(f"✅ Updated image_urls on {updated} product(s)")

        # Sample
        sample = products[:3]
        for p in sample:
            print(f"  {p.id}: {p.name[:40]:40s}  →  {len(p.image_urls) if is_json else len(_json.loads(p.image_urls))} images")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc(); sys.exit(1)
