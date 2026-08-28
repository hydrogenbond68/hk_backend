from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@example.com').first()
    
    if admin:
        print('Admin user already exists!')
    else:
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created successfully!')
        print('📧 Email: admin@example.com')
        print('🔑 Password: admin123')
