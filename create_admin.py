from app import create_app, db
from app.models import User

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(email='harykimsintertech@gmail.com').first()
        
        if admin:
            print(f"Admin user already exists with email: {admin.email}")
            # Update password just in case
            admin.set_password('HK-Intertech23#')
            admin.is_admin = True
            admin.is_verified = True
            db.session.commit()
            print("✅ Admin password updated and verified")
        else:
            # Create new admin
            admin = User(
                email='harykimsintertech@gmail.com',
                first_name='Harykims',
                last_name='Intertech',
                company_name='Harykims Intertech',
                phone='0712345678',
                address='Nairobi, Kenya',
                is_admin=True,
                is_verified=True
            )
            admin.set_password('HK-Intertech23#')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
        
        # Display admin info
        admin_check = User.query.filter_by(email='harykimsintertech@gmail.com').first()
        if admin_check:
            print("\n" + "="*50)
            print("ADMIN USER INFORMATION")
            print("="*50)
            print(f"📧 Email: {admin_check.email}")
            print(f"🔑 Password: HK-Intertech23#")
            print(f"👤 Name: {admin_check.first_name} {admin_check.last_name}")
            print(f"⭐ Admin: {admin_check.is_admin}")
            print(f"✅ Verified: {admin_check.is_verified}")
            print(f"🆔 User ID: {admin_check.id}")
            print("="*50)

if __name__ == '__main__':
    create_admin_user()
