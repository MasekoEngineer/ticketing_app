import pytest
from datetime import datetime, timedelta

from app import create_app
from models import db, User, Event, Booking, Notification


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'MAIL_SUPPRESS_SEND': True
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def organizer(app):
    user = User(full_name='Test Organizer', email='org@test.com', role='organizer')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def attendee(app):
    user = User(full_name='Test Attendee', email='attend@test.com', role='attendee')
    user.set_password('pass123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin(app):
    user = User(full_name='Test Admin', email='admin@test.com', role='admin')
    user.set_password('admin123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_attendee(client, attendee):
    client.post('/login', data={'email': attendee.email, 'password': 'pass123'}, follow_redirects=True)
    return attendee


@pytest.fixture
def logged_in_organizer(client, organizer):
    client.post('/login', data={'email': organizer.email, 'password': 'pass123'}, follow_redirects=True)
    return organizer


@pytest.fixture
def logged_in_admin(client, admin):
    client.post('/login', data={'email': admin.email, 'password': 'admin123'}, follow_redirects=True)
    return admin


@pytest.fixture
def sample_event(app, organizer):
    event = Event(
        title='Test Event',
        description='A test event',
        venue='Test Venue',
        event_date=datetime.now() + timedelta(days=10),
        capacity=100,
        price=25.0,
        organizer_id=organizer.id
    )
    db.session.add(event)
    db.session.commit()
    return event


@pytest.fixture
def sample_booking(app, attendee, sample_event):
    booking = Booking(
        user_id=attendee.id,
        event_id=sample_event.id,
        quantity=2,
        total_price=50.0,
        status='pending'
    )
    db.session.add(booking)
    db.session.commit()
    return booking