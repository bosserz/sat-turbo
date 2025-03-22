from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# Database configuration for PostgreSQL on Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/sat_practice')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    progress = db.Column(db.JSON, default=dict)

# Load questions
with open('questions.json', 'r') as f:
    questions_data = json.load(f)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            user = User(username=username, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/practice', methods=['GET', 'POST'])
def practice():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    topics = list(questions_data.keys())
    if request.method == 'POST':
        topic = request.form.get('topic')
        questions = questions_data[topic] if topic else random.sample(sum(questions_data.values(), []), 5)
        return render_template('practice.html', questions=questions, topics=topics)
    return render_template('practice.html', topics=topics)

@app.route('/test')
def full_test():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Simple simulation: 20 random questions
    all_questions = sum(questions_data.values(), [])
    test_questions = random.sample(all_questions, min(20, len(all_questions)))
    return render_template('test.html', questions=test_questions)

@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    answers = request.form
    score = 0
    total = len(answers)
    
    for q_id, answer in answers.items():
        for topic in questions_data.values():
            for q in topic:
                if str(q['id']) == q_id and q['correct'] == answer:
                    score += 1
    
    # Update progress
    if 'practice' not in user.progress:
        user.progress['practice'] = []
    user.progress['practice'].append({'score': score, 'total': total, 'date': str(db.func.now())})
    db.session.commit()
    
    flash(f'Score: {score}/{total}')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
