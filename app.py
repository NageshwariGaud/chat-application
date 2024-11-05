from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Database models for user and message history
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)

# Routes for registration and login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('chat'))
        return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Handle messages and rooms with SocketIO
@socketio.on('join')
def handle_join(data):
    join_room(data['room'])
    send(f"{data['username']} has joined the room.", to=data['room'])

@socketio.on('leave')
def handle_leave(data):
    leave_room(data['room'])
    send(f"{data['username']} has left the room.", to=data['room'])

@socketio.on('message')
def handle_message(data):
    msg = Message(username=data['username'], room=data['room'], content=data['message'])
    db.session.add(msg)
    db.session.commit()
    send({'username': data['username'], 'message': data['message']}, to=data['room'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will now run within the application context
    socketio.run(app, debug=True)

