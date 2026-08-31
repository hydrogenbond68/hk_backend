from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Find admin user
    admin = User.query.filter_by(email='admin@harykims.com').first()
    
    if admin:
        print(f"Found admin user: {admin.email}")
        # Reset password
        admin.set_password('admin123')
        db.session.commit()
        print("✅ Admin password reset successfully!")
        print("📧 Email: admin@harykims.com")
        print("🔑 Password: admin123")
    else:
        print("Admin user not found. Creating new admin...")
        admin = User(
            email='admin@harykims.com',
            first_name='Admin',
            last_name='Harykims',
            company_name='Harykims Intertech',
            phone='0712345678',
            address='Nairobi, Kenya',
            is_admin=True,
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully!")
        print("📧 Email: admin@harykims.com")
        print("🔑 Password: admin123")
    
    # Also create a test user if needed
    test_user = User.query.filter_by(email='test@harykims.com').first()
    if not test_user:
        test_user = User(
            email='test@harykims.com',
            first_name='Test',
            last_name='User',
            company_name='Test Company',
            phone='0723456789',
            address='Nairobi, Kenya',
            is_admin=False,
            is_verified=True
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test user created successfully!")
        print("📧 Email: test@harykims.com")
        print("🔑 Password: test123")
    
    # List all users
    users = User.query.all()
    print("\n📋 All users:")
    for u in users:
        print(f"  - {u.email} (Admin: {u.is_admin})")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(email='admin@harykims.com').first()
        
        if admin:
            print(f"Found admin user: {admin.email}")
            admin.set_password('admin123')
            db.session.commit()
            print("✅ Admin password reset successfully!")
        else:
            print("Creating new admin user...")
            admin = User(
                email='admin@harykims.com',
                first_name='Admin',
                last_name='Harykims',
                company_name='Harykims Intertech',
                phone='0712345678',
                address='Nairobi, Kenya',
                is_admin=True,
                is_verified=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
        
        print("\n📧 Admin: admin@harykims.com / admin123")
        
        # List all users
        users = User.query.all()
        print("\n📋 All users:")
        for u in users:
            print(f"  - {u.email} (Admin: {u.is_admin})")
