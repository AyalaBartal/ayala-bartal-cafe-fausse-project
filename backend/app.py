from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# PostgreSQL database URI format:
# postgresql://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://fausse_1:fausse_password_1@localhost:5432/fausse'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a table model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
# Create tables and insert first row
@app.before_request
def init_db():
    db.create_all()
    if not User.query.first():
        user = User(username="admin", email="admin@example.com")
        db.session.add(user)
        db.session.commit()   
        
@app.route('/user/first')
def index():
    user = User.query.first()
    return f"Hello, {user.username}!"        

@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify(message="Hello, World!")

if __name__ == '__main__':
    app.run(debug=True)