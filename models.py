from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='attendee')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    events = db.relationship('Event', backref='organizer', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='attendee', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_organizer(self):
        return self.role == 'organizer'

    def __repr__(self):
        return f'<User {self.email}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    venue = db.Column(db.String(150), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_types = db.relationship('TicketType', backref='event', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='event', lazy=True, cascade='all, delete-orphan')

    @property
    def total_capacity(self):
        return sum(t.capacity for t in self.ticket_types)

    @property
    def tickets_sold(self):
        return sum(t.tickets_sold for t in self.ticket_types)

    @property
    def tickets_available(self):
        return self.total_capacity - self.tickets_sold

    @property
    def is_sold_out(self):
        return self.tickets_available <= 0

    def __repr__(self):
        return f'<Event {self.title}>'


class TicketType(db.Model):
    __tablename__ = 'ticket_types'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)   # ordinary / vip / vvip
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    tickets_sold = db.Column(db.Integer, default=0)

    bookings = db.relationship('Booking', backref='ticket_type', lazy=True)

    @property
    def available(self):
        return self.capacity - self.tickets_sold

    @property
    def is_sold_out(self):
        return self.tickets_sold >= self.capacity

    def __repr__(self):
        return f'<TicketType {self.category} - ${self.price}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey('ticket_types.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Booking {self.id} - {self.quantity}x {self.ticket_type.category}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Notification to {self.recipient}: {self.subject}>'