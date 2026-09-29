from app import create_app
from models import db, User, Event

app = create_app()
with app.app_context():
    print('--- USERS ---')
    for u in User.query.all():
        print(f'{u.id} | {u.email} | {u.role}')

    print()
    print('--- EVENTS AND ORGANIZERS ---')
    for e in Event.query.all():
        print(f'Event {e.id}: {e.title} | organizer={e.organizer.email}')