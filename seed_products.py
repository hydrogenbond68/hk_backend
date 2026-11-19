"""
seed_products.py - Insert 50 realistic products, adapting to real schema.
Handles first_name/last_name (NOT NULL) on the User model.
Run from project root with venv active:   python seed_products.py
"""

import sys
import json
import random
import traceback
from datetime import datetime, timedelta
from decimal import Decimal

# ---- CONFIG ----
TARGET_COUNT   = 50
SELLER_EMAIL   = "harykimsintertech@gmail.com"
SELLER_NAME    = "Hary Kims"
SELLER_PASSWORD = "SellerPass123!"
RESET_EXISTING = False


CATALOG = [
    ("Electronics", "Phones", [
        "Samsung Galaxy A54 5G", "iPhone 13 128GB", "Tecno Spark 20 Pro",
        "Infinix Note 30", "Xiaomi Redmi Note 12", "Oppo Reno 8T",
        "Nokia G21", "Google Pixel 7a",
    ], (15000, 95000), {"brand": "varies", "warranty": "1 year"}),

    ("Electronics", "Laptops", [
        "HP EliteBook 840 G8", "Dell Latitude 7420", "Lenovo ThinkPad T14",
        "MacBook Air M2", "Asus VivoBook 15", "Acer Aspire 5",
    ], (45000, 180000), {"cpu": "Intel/AMD/Apple", "ram": "8-16GB", "storage": "256-512GB SSD"}),

    ("Electronics", "Accessories", [
        "Anker 20000mAh Power Bank", "JBL Tune 510BT Headphones",
        "Logitech MX Master 3S", "Sandisk 128GB Flash Drive",
        "Belkin USB-C Hub 7-in-1", "Samsung 25W Fast Charger",
    ], (800, 15000), {"warranty": "6-12 months"}),

    ("Fashion", "Men's Clothing", [
        "Cotton Oxford Shirt", "Slim Fit Chinos", "Leather Belt",
        "Casual Sneakers White", "Wool Blend Blazer", "Polo T-Shirt Navy",
    ], (1200, 8500), {"material": "cotton/leather", "sizes": "S-XXL"}),

    ("Fashion", "Women's Clothing", [
        "Floral Maxi Dress", "High-Waist Jeans", "Silk Blouse",
        "Leather Handbag", "Ankle Strap Heels", "Cotton Cardigan",
    ], (1500, 12000), {"sizes": "XS-XL", "material": "varies"}),

    ("Home & Kitchen", "Cookware", [
        "Non-Stick Frying Pan 28cm", "Cast Iron Skillet 10in",
        "Stainless Steel Pot Set", "Pressure Cooker 6L",
        "Electric Kettle 1.7L", "Blender 600W",
    ], (900, 9500), {"material": "steel/iron", "warranty": "1 year"}),

    ("Home & Kitchen", "Furniture", [
        "Wooden Study Desk", "Ergonomic Office Chair",
        "3-Seater Fabric Sofa", "Queen Size Bed Frame",
        "Bookshelf 5-Tier", "Bedside Table Oak",
    ], (4500, 45000), {"material": "wood/fabric", "assembly": "required"}),

    ("Sports & Outdoors", "Fitness", [
        "Adjustable Dumbbell Set 20kg", "Yoga Mat 6mm",
        "Resistance Band Set", "Skipping Rope Pro",
        "Foam Roller", "Kettlebell 12kg",
    ], (700, 12000), {"warranty": "6 months"}),

    ("Sports & Outdoors", "Outdoor Gear", [
        "Camping Tent 4-Person", "Sleeping Bag -5C",
        "LED Headlamp 800lm", "Hiking Backpack 40L",
        "Portable Camping Stove",
    ], (1500, 15000), {"warranty": "1 year"}),

    ("Groceries", "Beverages", [
        "Kenya AA Coffee Beans 500g", "Green Tea 100 Bags",
        "Bottled Water 6-Pack 1.5L", "Fresh Juice 1L",
    ], (150, 1500), {"origin": "Kenya", "organic": "varies"}),

    ("Groceries", "Snacks", [
        "Roasted Macadamia Nuts 250g", "Dark Chocolate 70% 100g",
        "Mixed Nuts Premium 500g", "Granola Bars 6-Pack",
    ], (200, 1200), {"organic": "varies"}),
]

IMG_POOL = [
    "https://unsplash.com/photos/a-close-up-of-a-laptop-on-a-table-GDvvWcMGP9k",
    "https://plus.unsplash.com/premium_photo-1681160405580-a68e9c4707f9?w=400&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
    "https://plus.unsplash.com/premium_photo-1681160405580-a68e9c4707f9?w=400&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"
   
]


def find_db(app):
    ext = app.extensions.get("sqlalchemy")
    if ext is not None and hasattr(ext, "create_all"):
        return ext
    for path in ("app.extensions", "app.database", "app.db"):
        try:
            m = __import__(path, fromlist=["db"])
            c = getattr(m, "db", None)
            if c and hasattr(c, "create_all"):
                return c
        except ImportError:
            continue
    return None


def find_class(name, modules):
    for path in modules:
        try:
            m = __import__(path, fromlist=[name])
            k = getattr(m, name, None)
            if k is not None:
                return k
        except ImportError:
            continue
    return None


def create_seller(db, User):
    """Create a seller user, respecting first_name/last_name NOT NULL constraints."""
    from werkzeug.security import generate_password_hash

    ucols = {c.name: c for c in User.__table__.columns}
    kw = {"email": SELLER_EMAIL}

    # first_name / last_name (NOT NULL on this schema)
    first, _, last = SELLER_NAME.partition(" ")
    if "first_name" in ucols:
        kw["first_name"] = first or "Hary"
    if "last_name" in ucols:
        kw["last_name"] = last or "Kims"

    # optional generic name column
    for c in ("full_name", "name", "username", "display_name"):
        if c in ucols:
            kw[c] = SELLER_NAME
            break

    # other string columns
    if "company_name" in ucols:
        kw["company_name"] = "Hary Kims Ltd"
    for c in ("phone", "address", "profile_image"):
        if c in ucols:
            kw[c] = ""

    # booleans
    if "is_admin" in ucols:
        kw["is_admin"] = False
    if "is_verified" in ucols:
        kw["is_verified"] = True
    if "role" in ucols:
        kw["role"] = "seller"
    for c in ("is_active", "active", "enabled"):
        if c in ucols:
            kw[c] = True
            break

    # password
    for pc in ("password_hash", "password", "hashed_password", "pw_hash"):
        if pc in ucols:
            kw[pc] = generate_password_hash(SELLER_PASSWORD)
            break

    user = User(**kw)
    db.session.add(user)
    db.session.commit()
    return user


def build_product_dict(Product, payload):
    """Filter payload to real columns; handle JSON vs TEXT coercion."""
    cols = {c.name: c for c in Product.__table__.columns}
    json_cols = set()
    for c in Product.__table__.columns:
        if "json" in type(c.type).__name__.lower():
            json_cols.add(c.name)

    out = {}
    for k, v in payload.items():
        if k not in cols:
            continue
        if k in json_cols:
            out[k] = v
        elif isinstance(v, (dict, list)):
            out[k] = json.dumps(v)
        else:
            out[k] = v
    return out


def main():
    from app import create_app
    app = create_app()

    db = find_db(app)
    if db is None:
        print("FAIL: could not locate db"); sys.exit(2)

    Product = find_class("Product", ("app.models", "app.models.product", "app.models.products", "models"))
    if Product is None:
        print("FAIL: could not locate Product model"); sys.exit(3)

    User = find_class("User", ("app.models", "app.models.user", "app.models.users", "models"))

    cols = {c.name: c for c in Product.__table__.columns}
    print("Product columns:", sorted(cols.keys()))

    with app.app_context():
        # --- find or create the seller ---
        seller = None
        if User is not None:
            seller = db.session.query(User).filter_by(email=SELLER_EMAIL).first()
            if seller is None:
                print(f"Creating seller user {SELLER_EMAIL} ...")
                seller = create_seller(db, User)
                print(f"OK: created seller (id={seller.id})")
            else:
                print(f"OK: using existing seller (id={seller.id})")

        # --- determine seller FK column name ---
        seller_col = None
        for c in ("seller_id", "user_id", "owner_id", "vendor_id"):
            if c in cols:
                seller_col = c
                break
        if seller_col is None:
            print("FAIL: no seller/user/owner column on Product.")
            print("Columns:", list(cols))
            sys.exit(4)
        if seller is None:
            print(f"FAIL: no seller available to set '{seller_col}'")
            sys.exit(5)
        print(f"OK: using column '{seller_col}' = {seller.id}")

        # --- optional reset ---
        if RESET_EXISTING:
            n = db.session.query(Product).filter(
                getattr(Product, seller_col) == seller.id
            ).delete()
            db.session.commit()
            print(f"OK: deleted {n} existing product(s)")

        # --- build product pool ---
        pool = []
        for cat, sub, names, (pmin, pmax), specs in CATALOG:
            for name in names:
                pool.append((cat, sub, name, pmin, pmax, specs))
        random.seed(42)
        random.shuffle(pool)
        chosen = pool[:TARGET_COUNT]

        # --- insert ---
        inserted = 0
        now = datetime.utcnow()
        for cat, sub, name, pmin, pmax, specs in chosen:
            price = round(random.uniform(pmin, pmax), -2)
            payload = {
                seller_col: seller.id,
                "name": name,
                "description": (
                    f"{name} — a quality {sub.lower()} item in our {cat} range. "
                    f"Carefully selected for durability and value. "
                    f"Ships within 2–4 business days across Kenya."
                ),
                "price": Decimal(str(price)),
                "category": cat,
                "sub_category": sub,
                "stock_quantity": random.randint(5, 500),
                "min_order_quantity": random.choice([1, 1, 1, 2, 5, 10]),
                "image_urls": random.sample(IMG_POOL, k=random.randint(2, 4)),
                "specifications": {**specs, "color": random.choice(
                    ["Black", "White", "Silver", "Blue", "Red"])},
                "is_featured": random.random() < 0.25,
                "is_active": True,
                "created_at": now - timedelta(days=random.randint(0, 90)),
                "updated_at": now - timedelta(days=random.randint(0, 30)),
            }
            kwargs = build_product_dict(Product, payload)
            try:
                db.session.add(Product(**kwargs))
                inserted += 1
            except TypeError as e:
                print(f"SKIP {name}: {e}")
                db.session.rollback()
                continue

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            print("FAIL: commit failed:")
            traceback.print_exc()
            sys.exit(6)

        from sqlalchemy import text
        total = db.session.execute(text("SELECT COUNT(*) FROM products")).scalar()
        featured = db.session.execute(text(
            "SELECT COUNT(*) FROM products WHERE is_active=1 AND is_featured=1"
        )).scalar()

        print()
        print("=" * 56)
        print(f"Inserted this run : {inserted}")
        print(f"Total in products : {total}")
        print(f"Featured & active : {featured}")
        print("=" * 56)
        print("Done. Refresh your storefront.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
