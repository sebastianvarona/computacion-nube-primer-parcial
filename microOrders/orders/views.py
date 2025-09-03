from flask import Flask, render_template
from orders.controllers.order_controller import order_controller
from db.db import db
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'secret123'
app.config.from_object('config.Config')
db.init_app(app)

# Registrando el blueprint del controlador de ordenes
app.register_blueprint(order_controller)
CORS(app, supports_credentials=True, origins=['http://192.168.80.3:5001', 'http://localhost:5001'])

if __name__ == '__main__':
    app.run()