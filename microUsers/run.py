from users.views import app
from db.db import db
from users.models.user_model import Users
import time
import sys

def create_tables_with_retry(max_retries=30, delay=2):
    """Create database tables with retry logic"""
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
                
                # Create admin user if it doesn't exist
                admin_user = Users.query.filter_by(username='admin').first()
                if not admin_user:
                    admin_user = Users(
                        name='Admin User',
                        email='admin@example.com',
                        username='admin',
                        password='admin123'
                    )
                    db.session.add(admin_user)
                    
                    # Add sample users
                    sample_users = [
                        Users(name='juan', email='juan@gmail.com', username='juan', password='123'),
                        Users(name='maria', email='maria@gmail.com', username='maria', password='456')
                    ]
                    for user in sample_users:
                        if not Users.query.filter_by(username=user.username).first():
                            db.session.add(user)
                    
                    db.session.commit()
                    print("Admin user and sample data created")
                else:
                    print("Admin user already exists")
                    
            print("Database tables created successfully")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Failed to connect to database after all retries")
                sys.exit(1)

if __name__ == '__main__':
    create_tables_with_retry()
    app.run(host='0.0.0.0',port=5002)
