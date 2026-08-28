from app import create_app, db
from app.models import User, Product, Order, OrderItem, Review, Inquiry, Wishlist
import json

def init_database():
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        print('✅ Database tables created successfully!')
        
        # Create admin user
        admin = User(
            email='admin@harykims.com',
            first_name='Admin',
            last_name='Harykims',
            company_name='Harykims Intertech',
            is_admin=True,
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create test seller
        seller = User(
            email='seller@harykims.com',
            first_name='John',
            last_name='Doe',
            company_name='Tech Supplies Ltd',
            is_admin=False,
            is_verified=True
        )
        seller.set_password('seller123')
        db.session.add(seller)
        db.session.commit()
        
        # Create sample products
        sample_products = [
            {
                'name': 'Premium Wireless Headphones',
                'description': 'High-quality wireless headphones with noise cancellation and 30-hour battery life.',
                'price': 149.99,
                'category': 'Electronics',
                'sub_category': 'Audio',
                'stock_quantity': 50,
                'min_order_quantity': 1,
                'image_urls': json.dumps(['/api/placeholder/400/400', '/api/placeholder/400/400']),
                'specifications': json.dumps({
                    'brand': 'SoundPro',
                    'model': 'SP-2000',
                    'battery': '30 hours',
                    'connectivity': 'Bluetooth 5.0'
                }),
                'is_featured': True
            },
            {
                'name': 'Ergonomic Office Chair',
                'description': 'Premium ergonomic office chair with lumbar support and adjustable height.',
                'price': 299.99,
                'category': 'Furniture',
                'sub_category': 'Office',
                'stock_quantity': 25,
                'min_order_quantity': 1,
                'image_urls': json.dumps(['/api/placeholder/400/400']),
                'specifications': json.dumps({
                    'material': 'Mesh and Steel',
                    'weight_capacity': '300 lbs',
                    'warranty': '5 years'
                }),
                'is_featured': True
            },
            {
                'name': 'Smart LED Light Bulbs (4-Pack)',
                'description': 'WiFi-enabled smart LED bulbs with color control and voice assistant compatibility.',
                'price': 39.99,
                'category': 'Smart Home',
                'sub_category': 'Lighting',
                'stock_quantity': 100,
                'min_order_quantity': 1,
                'image_urls': json.dumps(['/api/placeholder/400/400']),
                'specifications': json.dumps({
                    'wattage': '9W',
                    'lifespan': '25000 hours',
                    'compatibility': 'Alexa, Google Home'
                })
            },
            {
                'name': 'Stainless Steel Water Bottle',
                'description': 'Double-walled vacuum insulated water bottle keeps drinks cold for 24 hours.',
                'price': 29.99,
                'category': 'Home & Kitchen',
                'sub_category': 'Drinkware',
                'stock_quantity': 200,
                'min_order_quantity': 2,
                'image_urls': json.dumps(['/api/placeholder/400/400']),
                'specifications': json.dumps({
                    'capacity': '32 oz',
                    'material': 'Stainless Steel',
                    'insulation': 'Vacuum'
                })
            }
        ]
        
        for product_data in sample_products:
            product = Product(
                seller_id=seller.id,
                **product_data
            )
            db.session.add(product)
        
        db.session.commit()
        print('✅ Sample products created successfully!')
        print('✅ Database initialization complete!')
        print('\n📧 Admin: admin@harykims.com / admin123')
        print('📧 Seller: seller@harykims.com / seller123')
        print('\n🚀 Your Harykims Intertech platform is ready!')

if __name__ == '__main__':
    init_database()
