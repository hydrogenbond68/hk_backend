from app import create_app, db
from app.models import Product

app = create_app()
with app.app_context():
    count = Product.query.count()
    print(f"Total products in database: {count}")
    
    # Show category breakdown
    categories = db.session.query(Product.category, db.func.count()).group_by(Product.category).all()
    print("\nCategory Breakdown:")
    for category, count in categories:
        print(f"  - {category}: {count} products")
    
    # Show sample products
    sample = Product.query.limit(5).all()
    print("\nSample Products:")
    for p in sample:
        print(f"  - {p.name} (${p.price:.2f}) - {p.category}")
