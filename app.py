import os
from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define database models
class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    messages = db.relationship('Message', backref='thread', cascade='all, delete', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(2000), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    threads = Thread.query.all()
    selected_thread_id = request.args.get('thread_id')
    selected_thread = db.session.get(Thread, selected_thread_id) if selected_thread_id else (threads[-1] if threads else None)
    return render_template('chat.html', threads=threads, selected_thread=selected_thread)

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    thread_id = int(request.form['thread_id'])

    user_message = Message(thread_id=thread_id, role="user", content=message)
    db.session.add(user_message)
    db.session.commit()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}],
    )
    answer = response.choices[0].message["content"].strip()

    assistant_message = Message(thread_id=thread_id, role="assistant", content=answer)
    db.session.add(assistant_message)
    db.session.commit()

    return redirect(url_for('index', thread_id=thread_id))

@app.route('/new_thread', methods=['POST'])
def new_thread():
    new_thread = Thread()
    db.session.add(new_thread)
    db.session.commit()
    return redirect(url_for('index', thread_id=new_thread.id))

@app.route('/load_thread/<int:thread_id>')
def load_thread(thread_id):
    threads = Thread.query.all()
    selected_thread = db.session.get(Thread, thread_id)
    return render_template('chat.html', threads=threads, selected_thread=selected_thread)

@app.route('/delete_thread', methods=['POST'])
def delete_thread():
    thread_id = int(request.form['thread_id'])
    thread = db.session.get(Thread, thread_id)
    db.session.delete(thread)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
