from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///cafe_fausse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Customer(db.Model):
    __tablename__ = 'customers'
    
    customer_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    newsletter_signup = db.Column(db.Boolean, default=False)
    
    # Relationship
    reservations = db.relationship('Reservation', backref='customer', lazy=True)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    reservation_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    time_slot = db.Column(db.DateTime, nullable=False)
    table_number = db.Column(db.Integer, nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False)

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Café Fausse API is running'})

@app.route('/api/newsletter', methods=['POST'])
def newsletter_signup():
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name', '')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check if customer already exists
        existing_customer = Customer.query.filter_by(email=email).first()
        
        if existing_customer:
            existing_customer.newsletter_signup = True
            if name and not existing_customer.customer_name:
                existing_customer.customer_name = name
        else:
            new_customer = Customer(
                customer_name=name,
                email=email,
                newsletter_signup=True
            )
            db.session.add(new_customer)
        
        db.session.commit()
        return jsonify({'message': 'Successfully subscribed to newsletter!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations', methods=['POST'])
def make_reservation():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_name', 'email', 'time_slot', 'number_of_guests']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        time_slot = datetime.fromisoformat(data['time_slot'].replace('Z', '+00:00'))
        
        # Check table availability (assuming 30 tables total)
        existing_reservations = Reservation.query.filter_by(time_slot=time_slot).count()
        
        if existing_reservations >= 30:
            return jsonify({'error': 'No tables available for the selected time slot. Please choose another time.'}), 400
        
        # Find or create customer
        customer = Customer.query.filter_by(email=data['email']).first()
        
        if not customer:
            customer = Customer(
                customer_name=data['customer_name'],
                email=data['email'],
                phone_number=data.get('phone_number'),
                newsletter_signup=data.get('newsletter_signup', False)
            )
            db.session.add(customer)
            db.session.flush()  # Get the customer_id
        
        # Assign random table number (1-30)
        used_tables = [r.table_number for r in Reservation.query.filter_by(time_slot=time_slot).all()]
        available_tables = [i for i in range(1, 31) if i not in used_tables]
        table_number = random.choice(available_tables)
        
        # Create reservation
        reservation = Reservation(
            customer_id=customer.customer_id,
            time_slot=time_slot,
            table_number=table_number,
            number_of_guests=data['number_of_guests']
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        return jsonify({
            'message': 'Reservation confirmed!',
            'reservation_id': reservation.reservation_id,
            'table_number': table_number,
            'time_slot': time_slot.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    try:
        reservation = Reservation.query.get_or_404(reservation_id)
        customer = Customer.query.get(reservation.customer_id)
        
        return jsonify({
            'reservation_id': reservation.reservation_id,
            'customer_name': customer.customer_name,
            'email': customer.email,
            'phone_number': customer.phone_number,
            'time_slot': reservation.time_slot.isoformat(),
            'table_number': reservation.table_number,
            'number_of_guests': reservation.number_of_guests
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)
