from products.views import app
from db.db import db
from products.models.product_model import Products
import time
import sys
import os
from shared.consul_utils import register_service_with_consul

def create_tables_with_retry(max_retries=30, delay=2):
    """Create database tables with retry logic"""
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
                
                # Create sample products if they don't exist
                if Products.query.count() == 0:
                    sample_products = [
                        Products(name='pc', price=150, quantity=10),
                        Products(name='phone', price=100, quantity=20),
                        Products(name='tablet', price=80, quantity=15),
                        Products(name='laptop', price=300, quantity=8)
                    ]
                    for product in sample_products:
                        db.session.add(product)
                    
                    db.session.commit()
                    print("Sample products created")
                else:
                    print("Products already exist")
                    
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
    
    # Register with Consul
    service_name = os.getenv('SERVICE_NAME', 'microproducts')
    service_port = int(os.getenv('SERVICE_PORT', 5003))
    
    if register_service_with_consul(service_name, service_port):
        print(f"Service {service_name} registered with Consul successfully")
    else:
        print(f"Failed to register {service_name} with Consul")
    
    app.run(host='0.0.0.0', port=service_port)