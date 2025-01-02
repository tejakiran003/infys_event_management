from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user
from datetime import datetime
from flask import request, redirect, url_for, flash
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Azeem%40123@localhost:3306/flask_project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    mail_id = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)

# Event model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    event_description = db.Column(db.Text, nullable=True)
    contact_details = db.Column(db.String(100), nullable=False)
    event_size = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('events', lazy=True))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)  # Add this line
    num_people = db.Column(db.Integer, nullable=False)
    hall_type = db.Column(db.String(50), nullable=False)
    food_type = db.Column(db.String(50), nullable=False)
    food_menu = db.Column(db.String(50), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    hall_name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event = db.relationship('Event', backref=db.backref('bookings', lazy=True))
    hall = db.relationship('Hall', backref=db.backref('bookings', lazy=True))  # Add this line
    


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)
    screenshot = db.Column(db.String(100), nullable=True)
    booking = db.relationship('Booking', backref=db.backref('payments', lazy=True))

class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_booked = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def registration():
    return render_template('registration.html')

@app.route('/register/submit', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    re_password = request.form['re_password']
    mobile_number = request.form['mobile_number']
    mail_id = request.form['mail_id']
    city = request.form['city']
    state = request.form['state']

    if not username or not password or not re_password or not mobile_number or not mail_id:
        flash("All fields are required!", "danger")
        return redirect(url_for('registration'))

    if password != re_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for('registration'))

    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "danger")
        return redirect(url_for('registration'))

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, mobile_number=mobile_number,
                    mail_id=mail_id, city=city, state=state)
    db.session.add(new_user)
    db.session.commit()

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for('login'))

@app.route('/login/submit', methods=['POST'])
def login_submit():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    # Check if admin credentials
    admin_username = "admin"
    admin_password = "admin123"  # Admin credentials
    if username == admin_username and password == admin_password:
        session['is_admin'] = True
        flash('Admin logged in successfully!', 'success')
        return redirect(url_for('admin_events'))

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        flash('Logged in successfully!', 'success')
        return redirect(url_for('login'))
    else:
        flash('Invalid username or password!', 'danger')
        return redirect(url_for('login'))

@app.route('/events')
def events():
    if 'user_id' not in session:
        flash('Please log in to create or access your events.', 'danger')
        return redirect(url_for('login'))
    events = Event.query.filter_by(user_id=session['user_id']).all()
    return render_template('events.html', events=events)

@app.route('/events/new', methods=['GET', 'POST'])
def new_event():
    if 'user_id' not in session:
        flash('You need to log in to create an event!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        start_datetime = datetime.strptime(request.form['start_datetime'], '%Y-%m-%dT%H:%M')
        end_datetime = datetime.strptime(request.form['end_datetime'], '%Y-%m-%dT%H:%M')

        if start_datetime > end_datetime:
            flash('Start date cannot be greater than the end date!', 'danger')
            return redirect(url_for('new_event'))

        event = Event(
            name=request.form['name'],
            location=request.form['location'],
            event_type=request.form['event_type'],
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            event_description=request.form['event_description'],
            contact_details=request.form['contact_details'],
            event_size=request.form['event_size'],
            user_id=session['user_id']
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('user_hall', event_id=event.id))  # Redirecting with event_id

    return render_template('new_event.html')


@app.route('/bookings/<int:event_id>', methods=['GET', 'POST'])
def bookings(event_id):
    event = Event.query.get_or_404(event_id)  # Fetch event details
    halls = Hall.query.all()
    hall_id = request.args.get('hall_id')  # Get hall_id from query parameters
    hall_name = request.args.get('hall_name')  # Get the hall name from the query parameters
    hall = Hall.query.get_or_404(hall_id)  # Fetch hall details

    if request.method == 'POST':
        email = request.form['email']
        event_type = request.form['event_type']
        num_people = int(request.form['num_people'])
        hall_type = request.form['hall_type']
        food_type = request.form['food_type']
        food_menu = request.form['food_menu']
        hall = Hall.query.get(hall_id)
        if hall:
            hall_name = hall.name  # Get the hall name from the Hall table
        else:
            hall_name = None  # or some default value if hall is not found

        # Food and hall pricing
        food_prices = {"basic": 180, "standard": 230, "premium": 300}
        extra = 200 if food_type == "non-veg" else 0
        hall_cost = 10000 if hall_type == "ac" else 7000

        total_food_cost = (food_prices[food_menu] + extra) * num_people
        total_cost = total_food_cost + hall_cost

        

        # Create a booking record
        booking = Booking(
            event_id=event_id,
            hall_id=hall.id,  # Pass hall.id to the booking
            email=email,
            event_type=event_type,
            hall_type=hall_type,
            num_people=num_people,
            food_type=food_type,
            food_menu=food_menu,
            total_cost=total_cost,
            hall_name=hall_name  # Store the hall name
        )
        db.session.add(booking)
        db.session.commit()

        flash("Booking confirmed!", "success")
        session['booking_id'] = booking.id  # Store booking ID in session
        return redirect(url_for('summary'))  # Assuming you have a 'summary' route

    return render_template('bookings.html', event=event, halls=halls, hall_name=hall_name)


@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if 'booking_id' not in session:
        flash("No booking found.", "danger")
        return redirect(url_for('bookings'))

    booking = Booking.query.get(session['booking_id'])
    
    # Fetch the event associated with this booking
    event = Event.query.get(booking.event_id)

    if request.method == 'POST':
        payment_type = request.form.get('payment_type')
        screenshot = request.files.get('screenshot')

        if payment_type == 'online' and not screenshot:
            flash("Please upload a screenshot for online payment.")
            return redirect(url_for('summary'))

        # Save the screenshot if uploaded
        if screenshot:
            filename = screenshot.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            screenshot.save(filepath)

        # Create payment record
        payment = Payment(booking_id=booking.id, payment_type=payment_type, 
                          screenshot=filepath if screenshot else None)
        db.session.add(payment)
        db.session.commit()

        flash(f"Payment type selected: {payment_type}", "success")
        return redirect(url_for('summary'))

    # Display summary data, now include 'event' for rendering the event details
    return render_template('summary.html', 
                           event=event,  # Pass the event object to the template
                           num_people=booking.num_people,
                           food_type=booking.food_type,
                           food_cost=booking.total_cost - 10000,  # Assuming hall cost is fixed
                           hall_cost=10000 if booking.hall_type == "ac" else 7000,
                           total_cost=booking.total_cost)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)  # Clear admin session data
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Admin routes

@app.route('/admin/events')
def admin_events():
    if 'is_admin' not in session:
        flash('Please log in as admin.', 'danger')
        return redirect(url_for('login'))
    
    events = Event.query.all()  # Get all events for admin view
    bookings = Booking.query.all()  # Fetch all bookings
    payments = Payment.query.all()  # Fetch all payments
    users = User.query.all() 
    return render_template('admin_events.html', events=events,bookings=bookings,payments=payments,users=users)

@app.route('/admin/event/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'is_admin' not in session:
        flash('Please log in as admin.', 'danger')
        return redirect(url_for('login'))

    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin_events'))


# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'mdazeem1103@gmail.com'
app.config['MAIL_PASSWORD'] = 'kpzo opeg wrcm qwby'
app.config['MAIL_DEFAULT_SENDER'] = 'mdazeem1103@gmail.com'
mail = Mail(app)

@app.route('/send_email', methods=['POST'])
def send_email():
    email = request.form['email']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    message_content = request.form['message']

    try:
        msg = Message(
            subject="Appointment Details",
            recipients=[email],
            body=(f"Dear User,\n\n"
                  f"Here are the details of your appointment:\n"
                  f"Date: {appointment_date}\n"
                  f"Time: {appointment_time}\n\n"
                  f"Message:\n{message_content}\n\n"
                  f"Best regards,\nEvent Management Team")
        )
        mail.send(msg)
        flash("Email sent successfully!", "success")
    except Exception as e:
        flash(f"Failed to send email: {str(e)}", "danger")

    return redirect(url_for('admin_events'))  # Redirect back to the admin dashboard after sending email

@app.route('/admin/halls', methods=['GET', 'POST'])
def manage_halls():
    if request.method == 'POST':
        # Add new hall
        name = request.form['hall_name']
        description = request.form['hall_description']
        new_hall = Hall(name=name, description=description)
        db.session.add(new_hall)
        db.session.commit()
        return redirect(url_for('manage_halls'))
    halls = Hall.query.all()
    return render_template('halls.html', halls=halls)

@app.route('/admin/halls/update/<int:hall_id>', methods=['POST'])
def update_hall(hall_id):
    hall = Hall.query.get(hall_id)
    if hall:
        hall.name = request.form['hall_name']
        hall.description = request.form['hall_description']
        db.session.commit()
    return redirect(url_for('manage_halls'))

@app.route('/admin/halls/delete/<int:hall_id>', methods=['POST'])
def delete_hall(hall_id):
    hall = Hall.query.get(hall_id)
    if hall:
        db.session.delete(hall)
        db.session.commit()
    return redirect(url_for('manage_halls'))

@app.route('/halls')
def halls_page():
    halls = Hall.query.all()
    return render_template('halls.html', halls=halls)
@app.route('/user_hall/<int:event_id>', methods=['GET', 'POST'])
def user_hall(event_id):
    event = Event.query.get_or_404(event_id)  # Fetch event details using event_id
    halls = Hall.query.all()  # Get the list of halls
    
    # Handle the form submission for hall booking
    if request.method == 'POST':
        hall_id = request.form.get('hall_id')  # Get hall ID from form
        hall = Hall.query.get(hall_id)
        if hall and not hall.is_booked:
            hall.is_booked = True
            db.session.commit()
            flash("Hall booked successfully!", "success")
        else:
            flash("This hall is already booked.", "error")
        
        # Redirect to the bookings page to fill event details
        return redirect(url_for('bookings', event_id=event_id, hall_id=hall_id))

    return render_template('user_hall.html', event=event, halls=halls)

@app.route('/halls/book/<int:hall_id>', methods=['POST'])
def book_hall(hall_id):
    hall = Hall.query.get(hall_id)
    event_id = request.args.get('event_id')  # Get event_id from query parameters
    
    if hall and not hall.is_booked:
        hall.is_booked = True
        db.session.commit()
        flash("Booking confirmed!", "success")
        return redirect(url_for('bookings', event_id=event_id))  # Redirect to the 'bookings' page with event_id

    flash("This hall is already booked.", "error")
    return redirect(url_for('summary', event_id=event_id))  # Redirect back to bookings page


@app.route('/notifications')
def notifications():
    # Fetch user-specific notifications from the database
    if 'user_id' in session:
        user_id = session['user_id']
        user_notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        return render_template('notifications.html', notifications=user_notifications)
    return redirect(url_for('admin_events'))


@app.route('/send_notification', methods=['POST'])
def send_notification():
    if 'is_admin' not in session:
        flash('Please log in as admin.', 'danger')
        return redirect(url_for('login'))  # Ensure only admins can send notifications

    user_id = request.form['user_id']
    message = request.form['message']

    # Save the notification to the database
    notification = Notification(user_id=user_id, message=message, is_read=False)
    db.session.add(notification)
    db.session.commit()

    flash('Notification sent successfully!', 'success')
    return redirect(url_for('admin_events'))


if __name__ == '__main__':
    app.run(debug=True)
