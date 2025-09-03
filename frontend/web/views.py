from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import logging
from shared.consul_utils import get_consul_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'secret123'
CORS(app, supports_credentials=True)
app.config.from_object('config.Config')


# Ruta para renderizar el template index.html
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Ruta para renderizar el template users.html
@app.route('/users')
def users():
    return render_template('users.html')

# Ruta para renderizar el template products.html
@app.route('/products')
def products():
    return render_template('products.html')

# Ruta para renderizar el template orders.html
@app.route('/orders')
def orders():
    return render_template('orders.html')

@app.route('/editUser/<string:id>')
def edit_user(id):
    print("id recibido",id)
    return render_template('editUser.html', id=id)

@app.route('/editProduct/<string:id>')
def edit_product(id):
    print("id recibido",id)
    return render_template('editProduct.html', id=id)

@app.route('/editOrder/<string:id>')
def edit_order(id):
    print("id recibido",id)
    return render_template('editOrder.html', id=id)

def map_service_to_external_url(service_name, internal_url):
    """Map internal service URL to external URL accessible from browser"""
    # Map service names to external ports
    port_mapping = {
        'microusers': '5002',
        'microproducts': '5003', 
        'microorders': '5004'
    }
    
    if service_name in port_mapping:
        # Get the host IP from the current request
        host_ip = request.host.split(':')[0]  # Remove port if present
        return f"http://{host_ip}:{port_mapping[service_name]}"
    
    return internal_url  # fallback

@app.route('/api/services/<service_name>')
def get_service_url(service_name):
    """API endpoint to get service URL via Consul service discovery"""
    try:
        consul_client = get_consul_client()
        internal_url = consul_client.get_service_url(service_name)
        
        if internal_url:
            # Map to external URL accessible from browser
            external_url = map_service_to_external_url(service_name, internal_url)
            return jsonify({
                'status': 'success',
                'service_name': service_name,
                'url': external_url,
                'internal_url': internal_url
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Service {service_name} not found'
            }), 404
    except Exception as e:
        logger.error(f"Error discovering service {service_name}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/services')
def get_all_services():
    """Get all available services"""
    try:
        consul_client = get_consul_client()
        services = {}
        
        # Try to discover each expected service
        service_names = ['microusers', 'microproducts', 'microorders']
        for service_name in service_names:
            internal_url = consul_client.get_service_url(service_name)
            if internal_url:
                # Map to external URL accessible from browser
                external_url = map_service_to_external_url(service_name, internal_url)
                services[service_name] = external_url
        
        return jsonify({
            'status': 'success',
            'services': services
        }), 200
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run()
