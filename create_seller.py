from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Check if seller exists
    seller = User.query.filter_by(email='seller@harykims.com').first()
    if not seller:
        seller = User(
            email='seller@harykims.com',
            first_name='John',
            last_name='Doe',
            company_name='Harykims Intertech Supplies',
            phone='+1234567890',
            address='123 Business Street, City, Country',
            is_admin=False,
            is_verified=True
        )
        seller.set_password('seller123')
        db.session.add(seller)
        db.session.commit()
        print('✅ Seller created successfully!')
        print('📧 Email: seller@harykims.com')
        print('🔑 Password: seller123')
    else:
        print('✅ Seller already exists with ID:', seller.id)
        print('📧 Email: seller@harykims.com')
