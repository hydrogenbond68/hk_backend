from app import create_app, db
from app.models import User, Product, Order, OrderItem, Review, Inquiry, Wishlist
import sqlite3
import os

def migrate_database():
    app = create_app()
    with app.app_context():
        # Check if we need to add new columns
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'harykims.db')
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users table columns
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Add new columns if they don't exist
            new_columns = ['reset_token', 'reset_token_expiry', 'updated_at']
            for col in new_columns:
                if col not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(100)")
                        print(f"✅ Added column: {col}")
                    except Exception as e:
                        print(f"⚠️ Could not add column {col}: {e}")
            
            conn.commit()
            conn.close()
            print("✅ Database migration completed!")
        else:
            print("⚠️ Database not found. Creating new database...")
            db.create_all()
            print("✅ New database created!")

if __name__ == '__main__':
    migrate_database()
