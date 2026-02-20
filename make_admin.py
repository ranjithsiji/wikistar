import sys
from app import create_app
from extensions import db
from models import User

def make_admin(username):
    app = create_app()
    with app.app_context():
        # Find the user by username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"Error: User '{username}' not found in the database.")
            print("Please ensure you have logged in via Wikimedia OAuth at least once.")
            sys.exit(1)
            
        # Update role to admin
        user.role = 'admin'
        db.session.commit()
        print(f"Success! '{username}' has been promoted to Admin.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <your_wikimedia_username>")
        sys.exit(1)
        
    target_username = sys.argv[1]
    make_admin(target_username)
