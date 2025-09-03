from db.db import db
from datetime import datetime

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(255), nullable=True)
    userEmail = db.Column(db.String(255), nullable=True)
    saleTotal = db.Column(db.Numeric(10, 2), nullable=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    def __init__(self, userName, userEmail, saleTotal, date=None):
        self.userName = userName
        self.userEmail = userEmail
        self.saleTotal = saleTotal
        if date:
            self.date = date