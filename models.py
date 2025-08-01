# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class QueryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(20))
    case_no = db.Column(db.String(20))
    filing_year = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime)
    raw_response = db.Column(db.Text)
    error_message = db.Column(db.Text)