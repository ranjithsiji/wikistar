"""
Migration: Expand the 'role' ENUM in the users table to include 'coordinator' and 'user'.
Run this once to update the live database schema.
"""
from app import create_app
from extensions import db

def run_migration():
    app = create_app()
    with app.app_context():
        try:
            sql = """
                ALTER TABLE users 
                MODIFY COLUMN role ENUM('admin', 'coordinator', 'jury', 'user', 'participant') 
                DEFAULT 'participant';
            """
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✅ Migration successful: 'role' ENUM updated to include 'coordinator' and 'user'.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")

if __name__ == '__main__':
    run_migration()
