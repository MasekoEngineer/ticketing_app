from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, TextAreaField,
                     IntegerField, FloatField, DateTimeLocalField, SelectField)
from wtforms.validators import (DataRequired, Email, Length, NumberRange,
                                EqualTo, ValidationError)
from datetime import datetime


class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField('Register As', choices=[('attendee', 'Attendee'), ('organizer', 'Organizer')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired(), Length(min=3, max=150)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    venue = StringField('Venue', validators=[DataRequired(), Length(min=3, max=150)])
    event_date = DateTimeLocalField(
        'Event Date & Time',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )
    submit = SubmitField('Save Event')

    def validate_event_date(self, event_date):
        if event_date.data <= datetime.now():
            raise ValidationError('Event date must be in the future.')


class TicketTypeForm(FlaskForm):
    category = SelectField('Category', choices=[
        ('ordinary', 'Ordinary'),
        ('vip', 'VIP'),
        ('vvip', 'VVIP')
    ], validators=[DataRequired()])
    price = FloatField('Price (USD)', validators=[DataRequired(), NumberRange(min=0.0, max=10000.0)])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=10000)])
    submit = SubmitField('Add Ticket Type')


class BookingForm(FlaskForm):
    ticket_type_id = SelectField('Ticket Category', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Number of Tickets',
                            validators=[DataRequired(),
                                        NumberRange(min=1, max=10,
                                                    message='Quantity must be between 1 and 10')])
    submit = SubmitField('Book Now')


class SearchForm(FlaskForm):
    query = StringField('Search Events')
    submit = SubmitField('Search')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')


class RejectBookingForm(FlaskForm):
    reason = TextAreaField(
        'Reason for Rejection',
        validators=[
            DataRequired(message='You must provide a reason for rejecting this booking.'),
            Length(min=5, max=500, message='Reason must be between 5 and 500 characters.')
        ],
        render_kw={
            'rows': 4,
            'placeholder': 'Explain why this booking is being rejected (required)...'
        }
    )
    submit = SubmitField('Confirm Rejection')