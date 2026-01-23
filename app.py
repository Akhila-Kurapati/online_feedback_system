from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def get_db_connection():
    conn = sqlite3.connect('feedback.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    time = datetime.now().strftime("%d-%m-%Y %H:%M")

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO feedback (name, email, message, created_at) VALUES (?, ?, ?, ?)',
        (name, email, message, time)
    )
    conn.commit()
    conn.close()
    return render_template('success.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        else:
            error = "Invalid Credentials"
    return render_template('admin_login.html', error=error)

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/admin_login')

    search = request.args.get('search')
    conn = get_db_connection()

    if search:
        feedbacks = conn.execute(
            "SELECT * FROM feedback WHERE name LIKE ? OR email LIKE ?",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        feedbacks = conn.execute('SELECT * FROM feedback').fetchall()

    conn.close()
    return render_template('admin.html', feedbacks=feedbacks)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    feedback = conn.execute(
        'SELECT * FROM feedback WHERE id = ?', (id,)
    ).fetchone()

    if request.method == 'POST':
        message = request.form['message']
        conn.execute(
            'UPDATE feedback SET message = ? WHERE id = ?',
            (message, id)
        )
        conn.commit()
        conn.close()
        return redirect('/admin')

    conn.close()
    return render_template('edit.html', feedback=feedback)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    conn.execute('DELETE FROM feedback WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/admin_login')

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TEXT
        )
    ''')
    conn.close()
    app.run(debug=True)