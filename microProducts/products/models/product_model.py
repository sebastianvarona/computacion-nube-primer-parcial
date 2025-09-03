from db.db import db

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Integer, nullable=True)
    quantity = db.Column(db.Integer, nullable=True)

    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity