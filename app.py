import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from datetime import datetime
from sqlalchemy import or_
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
#from flask_wtf.csrf import CSRFProtect

from models import db, User, Event, Booking, TicketType, Notification
from forms import (RegistrationForm, LoginForm, EventForm, TicketTypeForm, BookingForm,
                   ForgotPasswordForm, ResetPasswordForm, RejectBookingForm)


def create_app(config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'peniatest@gmail.com'
    app.config['MAIL_PASSWORD'] = 'cjwf dprh otrh sxiy'
    app.config['MAIL_DEFAULT_SENDER'] = 'peniatest@gmail.com'

    if config:
        app.config.update(config)

    db.init_app(app)
    #csrf = CSRFProtect(app)
    mail = Mail(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------- Password Reset Tokens ----------
    def generate_reset_token(email):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='password-reset-salt')

    def verify_reset_token(token, expiration=3600):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        except (SignatureExpired, BadSignature):
            return None
        return email

    # ---------- Email ----------
    def simulate_email(recipient, subject, body):
        notification = Notification(recipient=recipient, subject=subject, body=body, sent=False)
        db.session.add(notification)
        db.session.commit()
        try:
            msg = Message(subject=subject, recipients=[recipient], body=body)
            mail.send(msg)
            notification.sent = True
            db.session.commit()
            print(f"\n[EMAIL SENT] To: {recipient} | Subject: {subject}\n")
        except Exception as e:
            print(f"\n[EMAIL FAILED] To: {recipient} | Error: {e}\n")

    # ---------- Auth ----------
    @app.route('/')
    def home():
        events = Event.query.filter(Event.event_date > datetime.now()).order_by(Event.event_date).limit(6).all()
        return render_template('home.html', events=events)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = RegistrationForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('register'))
            user = User(full_name=form.full_name.data, email=form.email.data.lower(), role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash(f'Welcome back, {user.full_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            flash('Invalid email or password.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user:
                token = generate_reset_token(user.email)
                reset_url = url_for('reset_password', token=token, _external=True)
                simulate_email(user.email, 'TicketHub Password Reset',
                               f'Hi {user.full_name},\n\nReset your password:\n\n{reset_url}\n\nExpires in 1 hour.')
            flash('If that email is registered, a reset link has been sent.', 'info')
            return redirect(url_for('login'))
        return render_template('forgot_password.html', form=form)

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        email = verify_reset_token(token)
        if not email:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('forgot_password'))
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('forgot_password'))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            db.session.commit()
            flash('Your password has been reset. You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('reset_password.html', form=form)

    # ---------- Events ----------
    @app.route('/events')
    def events():
        query = request.args.get('q', '').strip()
        if query:
            events_list = Event.query.filter(
                or_(Event.title.ilike(f'%{query}%'), Event.venue.ilike(f'%{query}%'))
            ).order_by(Event.event_date).all()
        else:
            events_list = Event.query.order_by(Event.event_date).all()
        return render_template('events.html', events=events_list, query=query)

    @app.route('/events/<int:event_id>')
    def event_detail(event_id):
        event = Event.query.get_or_404(event_id)
        return render_template('event_detail.html', event=event)

    @app.route('/events/create', methods=['GET', 'POST'])
    @login_required
    def create_event():
        if not current_user.is_organizer():
            flash('Only organizers can create events.', 'danger')
            return redirect(url_for('events'))
        form = EventForm()
        if form.validate_on_submit():
            event = Event(
                title=form.title.data,
                description=form.description.data,
                venue=form.venue.data,
                event_date=form.event_date.data,
                organizer_id=current_user.id
            )
            db.session.add(event)
            db.session.commit()
            flash('Event created! Now add ticket types.', 'success')
            return redirect(url_for('manage_ticket_types', event_id=event.id))
        return render_template('create_event.html', form=form)

    @app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_event(event_id):
        event = Event.query.get_or_404(event_id)
        if event.organizer_id != current_user.id:
            abort(403)
        form = EventForm(obj=event)
        if form.validate_on_submit():
            form.populate_obj(event)
            db.session.commit()
            flash('Event updated.', 'success')
            return redirect(url_for('event_detail', event_id=event.id))
        return render_template('create_event.html', form=form, editing=True)

    @app.route('/events/<int:event_id>/delete', methods=['POST'])
    @login_required
    def delete_event(event_id):
        event = Event.query.get_or_404(event_id)
        if event.organizer_id != current_user.id:
            abort(403)
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted.', 'info')
        return redirect(url_for('my_events'))

    @app.route('/my-events')
    @login_required
    def my_events():
        if not current_user.is_organizer():
            flash('Only organizers have events.', 'warning')
            return redirect(url_for('home'))
        events_list = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.event_date).all()
        return render_template('my_events.html', events=events_list)

    # ---------- Ticket Types ----------
    @app.route('/events/<int:event_id>/ticket-types', methods=['GET', 'POST'])
    @login_required
    def manage_ticket_types(event_id):
        event = Event.query.get_or_404(event_id)
        if event.organizer_id != current_user.id:
            abort(403)
        form = TicketTypeForm()
        if form.validate_on_submit():
            existing = TicketType.query.filter_by(event_id=event.id, category=form.category.data).first()
            if existing:
                flash(f'{form.category.data.upper()} already exists for this event.', 'warning')
                return redirect(url_for('manage_ticket_types', event_id=event.id))
            tt = TicketType(
                event_id=event.id,
                category=form.category.data,
                price=form.price.data,
                capacity=form.capacity.data
            )
            db.session.add(tt)
            db.session.commit()
            flash(f'{form.category.data.upper()} ticket type added.', 'success')
            return redirect(url_for('manage_ticket_types', event_id=event.id))
        return render_template('manage_ticket_types.html', event=event, form=form)

    @app.route('/ticket-types/<int:tt_id>/delete', methods=['POST'])
    @login_required
    def delete_ticket_type(tt_id):
        tt = TicketType.query.get_or_404(tt_id)
        if tt.event.organizer_id != current_user.id:
            abort(403)
        if tt.tickets_sold > 0:
            flash('Cannot delete a ticket type that has bookings.', 'danger')
            return redirect(url_for('manage_ticket_types', event_id=tt.event_id))
        db.session.delete(tt)
        db.session.commit()
        flash('Ticket type deleted.', 'info')
        return redirect(url_for('manage_ticket_types', event_id=tt.event_id))

    # ---------- Bookings ----------
    @app.route('/events/<int:event_id>/book', methods=['GET', 'POST'])
    @login_required
    def book_ticket(event_id):
        event = Event.query.get_or_404(event_id)
        if event.organizer_id == current_user.id:
            flash('You cannot book your own event.', 'warning')
            return redirect(url_for('event_detail', event_id=event.id))

        form = BookingForm()
        form.ticket_type_id.choices = [
            (t.id, f'{t.category.upper()} - ${t.price:.2f} ({t.available} left)')
            for t in event.ticket_types if not t.is_sold_out
        ]

        if not form.ticket_type_id.choices:
            flash('No tickets available for this event.', 'danger')
            return redirect(url_for('event_detail', event_id=event.id))

        if form.validate_on_submit():
            tt = TicketType.query.get(form.ticket_type_id.data)
            if not tt or tt.event_id != event.id:
                flash('Invalid ticket type.', 'danger')
                return redirect(url_for('book_ticket', event_id=event.id))

            qty = form.quantity.data
            if qty < 1 or qty > 10:
                flash('Quantity must be between 1 and 10.', 'danger')
                return redirect(url_for('book_ticket', event_id=event.id))
            if event.event_date <= datetime.now():
                flash('This event has already passed.', 'danger')
                return redirect(url_for('event_detail', event_id=event.id))
            if tt.tickets_sold + qty > tt.capacity:
                flash(f'Only {tt.available} {tt.category.upper()} ticket(s) available.', 'danger')
                return redirect(url_for('book_ticket', event_id=event.id))

            booking = Booking(
                user_id=current_user.id,
                event_id=event.id,
                ticket_type_id=tt.id,
                quantity=qty,
                total_price=qty * tt.price,
                status='pending'
            )
            db.session.add(booking)
            db.session.commit()

            simulate_email(event.organizer.email, f'New Booking for Your Event: {event.title}',
                           f'{current_user.full_name} ({current_user.email}) requested {qty} {tt.category.upper()} ticket(s) '
                           f'for "{event.title}" (Booking ID: {booking.id}). Total: ${booking.total_price:.2f}.')

            admins = User.query.filter_by(role='admin').all()
            for admin in admins:
                approve_url = url_for('admin_bookings', _external=True)
                simulate_email(
                    admin.email,
                    f'Booking Approval Needed: {event.title}',
                    f'{current_user.full_name} requested {qty} {tt.category.upper()} ticket(s) '
                    f'for "{event.title}" (Booking ID: {booking.id}).\n\n'
                    f'Please review and approve:\n{approve_url}'
                )

            flash('Booking submitted. Awaiting admin approval.', 'info')
            return redirect(url_for('my_bookings'))
        return render_template('book_ticket.html', form=form, event=event)

    @app.route('/my-bookings')
    @login_required
    def my_bookings():
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()
        return render_template('my_bookings.html', bookings=bookings)

    @app.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
    @login_required
    def cancel_booking(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        if booking.user_id != current_user.id:
            abort(403)
        if booking.status == 'cancelled':
            flash('Booking already cancelled.', 'info')
            return redirect(url_for('my_bookings'))
        if booking.status == 'pending':
            flash('Cannot cancel a pending booking.', 'warning')
            return redirect(url_for('my_bookings'))
        booking.status = 'cancelled'
        booking.ticket_type.tickets_sold -= booking.quantity
        db.session.commit()
        flash('Booking cancelled.', 'info')
        return redirect(url_for('my_bookings'))

    # ---------- Reports ----------
    @app.route('/reports')
    @login_required
    def reports():
        if not current_user.is_organizer():
            flash('Only organizers can access reports.', 'danger')
            return redirect(url_for('home'))
        events_list = Event.query.filter_by(organizer_id=current_user.id).all()
        report_data = []
        for ev in events_list:
            categories = []
            for tt in ev.ticket_types:
                confirmed = [b for b in tt.bookings if b.status == 'confirmed']
                categories.append({
                    'category': tt.category,
                    'sold': sum(b.quantity for b in confirmed),
                    'capacity': tt.capacity,
                    'revenue': sum(b.total_price for b in confirmed)
                })
            report_data.append({'event': ev, 'categories': categories,
                                'total_revenue': sum(c['revenue'] for c in categories)})
        return render_template('reports.html', report_data=report_data)

    # ---------- Admin ----------
    @app.route('/admin/bookings')
    @login_required
    def admin_bookings():
        if current_user.role != 'admin':
            abort(403)
        pending = Booking.query.filter_by(status='pending').order_by(Booking.booked_at.desc()).all()
        all_bookings = Booking.query.order_by(Booking.booked_at.desc()).limit(50).all()
        reject_form = RejectBookingForm()  # ← Provide a CSRF-valid form instance
        return render_template('admin_bookings.html',
                               pending=pending,
                               all_bookings=all_bookings,
                               reject_form=reject_form)

    @app.route('/admin/bookings/<int:booking_id>/approve', methods=['POST'])
    @login_required
    def approve_booking(booking_id):
        if current_user.role != 'admin':
            abort(403)
        booking = Booking.query.get_or_404(booking_id)
        if booking.status != 'pending':
            flash('Only pending bookings can be approved.', 'warning')
            return redirect(url_for('admin_bookings'))
        tt = booking.ticket_type
        if tt.tickets_sold + booking.quantity > tt.capacity:
            flash(f'Cannot approve: only {tt.available} {tt.category.upper()} ticket(s) left.', 'danger')
            return redirect(url_for('admin_bookings'))
        booking.status = 'confirmed'
        tt.tickets_sold += booking.quantity
        db.session.commit()
        simulate_email(booking.attendee.email, f'Booking Confirmed: {booking.event.title}',
                       f'Hi {booking.attendee.full_name}, your {booking.quantity} {tt.category.upper()} ticket(s) '
                       f'to "{booking.event.title}" are CONFIRMED. Total: ${booking.total_price:.2f}.')
        flash(f'Booking #{booking.id} approved.', 'success')
        return redirect(url_for('admin_bookings'))

    @app.route('/admin/bookings/<int:booking_id>/reject', methods=['POST'])
    @login_required
    def reject_booking(booking_id):
        if current_user.role != 'admin':
            abort(403)

        booking = Booking.query.get_or_404(booking_id)
        if booking.status != 'pending':
            flash('Only pending bookings can be rejected.', 'warning')
            return redirect(url_for('admin_bookings'))

        form = RejectBookingForm()
        if form.validate_on_submit():
            reason = form.reason.data.strip()

            booking.status = 'rejected'
            booking.rejection_reason = reason
            db.session.commit()

            simulate_email(
                booking.attendee.email,
                f'Booking Rejected: {booking.event.title}',
                f'Hi {booking.attendee.full_name},\n\n'
                f'Unfortunately your booking for {booking.quantity} '
                f'{booking.ticket_type.category.upper()} ticket(s) to '
                f'"{booking.event.title}" has been REJECTED.\n\n'
                f'Reason provided by admin:\n'
                f'----------------------------------------\n'
                f'{reason}\n'
                f'----------------------------------------\n\n'
                f'If you believe this is a mistake, please contact the organizer.'
            )

            flash(f'Booking #{booking.id} rejected.', 'info')
            return redirect(url_for('admin_bookings'))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
        return redirect(url_for('admin_bookings'))

    @app.route('/admin/notifications')
    @login_required
    def admin_notifications():
        if current_user.role != 'admin':
            abort(403)
        notifications = Notification.query.order_by(Notification.sent_at.desc()).limit(100).all()
        return render_template('admin_notifications.html', notifications=notifications)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)