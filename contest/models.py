from datetime import datetime, UTC
from flask_login import UserMixin
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class Athlete(db.Model):  # pylint: disable=too-few-public-methods
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    country = db.Column(db.String(64))
    access_token = db.Column(db.String(256))
    refresh_token = db.Column(db.String(256))
    expires_at = db.Column(db.Integer)
    activities = db.relationship('Activity', backref='athlete', lazy='dynamic')
    points = db.relationship('Point', backref='athlete', lazy='dynamic')

    def to_dict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class Activity(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athlete.id'))
    name = db.Column(db.String(255))
    distance = db.Column(db.Float)
    moving_time = db.Column(db.Integer)
    elapsed_time = db.Column(db.Integer)
    start_date = db.Column(db.DateTime, index=True)
    total_elevation_gain = db.Column(db.Integer)
    type = db.Column(db.String(20))
    has_map = db.Column(db.Integer, default=0)
    polyline = db.Column(db.String)
    photo_count = db.Column(db.Integer)

    def __repr__(self):
        return f'<Activity {self.name}>'

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "name": self.name,
            "distance": self.distance,
            "moving_time": self.moving_time,
            "elapsed_time": self.elapsed_time,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "total_elevation_gain": self.total_elevation_gain,
            "type": self.type,
            "has_map": self.has_map,
            "polyline": self.polyline,
            "photo_count": self.photo_count,
        }


class Point(db.Model):
    year = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athlete.id'), primary_key=True)
    total_points = db.Column(db.Integer)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athlete.id'), nullable=True)
    athlete = db.relationship('Athlete', backref='users', uselist=False)
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
