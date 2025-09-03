from orders.views import app
from db.db import db
from orders.models.order_model import Orders
import time
import sys

def create_tables_with_retry(max_retries=30, delay=2):
    """Create database tables with retry logic"""
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
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
    app.run(host='0.0.0.0',port=5004)
