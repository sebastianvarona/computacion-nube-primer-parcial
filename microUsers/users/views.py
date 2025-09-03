from flask import Flask, render_template, jsonify
from users.controllers.user_controller import user_controller
from db.db import db
from flask_cors import CORS
import os
import logging
from shared.consul_utils import register_service_with_consul

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'secret123'
app.config.from_object('config.Config')
db.init_app(app)

# Registrando el blueprint del controlador de usuarios
app.register_blueprint(user_controller)
CORS(app, supports_credentials=True, origins=['http://192.168.80.3:5001', 'http://localhost:5001'])

@app.route('/health')
def health_check():
    """Health check endpoint for Consul"""
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy", "service": "microusers"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "service": "microusers", "error": str(e)}), 500

if __name__ == '__main__':
    app.run()
