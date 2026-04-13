from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
import bcrypt

# ---------------- PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = "secret123"

# ---------------- DB (SQLITE) ----------------
db = sqlite3.connect('hostel.db', check_same_thread=False)
cursor = db.cursor()
print("✅ Connected to SQLite")


# ---------------- CREATE TABLES ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    room_no TEXT,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS wardens (
    warden_id TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS helpdesk (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_type TEXT,
    description TEXT,
    room_no TEXT,
    student_id TEXT,
    student_name TEXT,
    status TEXT,
    worker_id TEXT
)
""")

# default users
cursor.execute("INSERT OR IGNORE INTO wardens VALUES ('1', '123')")
cursor.execute("INSERT OR IGNORE INTO workers VALUES ('1', '123')")

db.commit()


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('login.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    role = request.form['role']
    user_id = request.form['user_id']
    password = request.form['password']

    if role == 'student':
        cursor.execute("SELECT * FROM students WHERE student_id=?", (user_id,))
        user = cursor.fetchone()

        if user:
            stored_password = user[4]  # adjust index if needed

            if isinstance(stored_password, str):
                stored_password = stored_password.encode()

            if bcrypt.checkpw(password.encode(), stored_password):
                session['user'] = user_id
                session['role'] = 'student'
                return redirect('/student')

    elif role == 'warden':
        cursor.execute("SELECT * FROM wardens WHERE warden_id=? AND password=?", (user_id, password))
        if cursor.fetchone():
            session['user'] = user_id
            session['role'] = 'warden'
            return redirect('/warden')

    elif role == 'worker':
        cursor.execute("SELECT * FROM workers WHERE worker_id=? AND password=?", (user_id, password))
        if cursor.fetchone():
            session['user'] = user_id
            session['role'] = 'worker'
            return redirect('/worker')

    return render_template('login.html', error="User not found or incorrect password")


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        reg = request.form['reg']
        phone = request.form['phone']
        room = request.form['room']
        password = request.form['password']

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO students (student_id, name, phone, room_no, password)
            VALUES (?, ?, ?, ?, ?)
        """, (reg, name, phone, room, hashed_password))

        db.commit()
        return redirect('/')

    return render_template('register.html')


# ---------------- STUDENT ----------------
@app.route('/student')
def student():
    if 'user' not in session:
        return redirect('/')

    student_id = session['user']

    cursor.execute("SELECT name, room_no FROM students WHERE student_id=?", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM helpdesk WHERE student_id=?", (student_id,))
    complaints = cursor.fetchall()

    return render_template('student_dashboard.html',
                           complaints=complaints,
                           student_name=student[0],
                           student_id=student_id,
                           room_no=student[1])


# ---------------- SUBMIT COMPLAINT ----------------
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user' not in session:
        return redirect('/')

    student_id = session['user']

    cursor.execute("SELECT room_no FROM students WHERE student_id=?", (student_id,))
    room_no = cursor.fetchone()[0]

    student_name = request.form['student_name']
    issue_type = request.form['issue_type']

    cursor.execute("""
        INSERT INTO helpdesk 
        (issue_type, description, room_no, student_id, student_name, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (issue_type, "", room_no, student_id, student_name, "pending"))

    db.commit()
    return redirect('/student')


# ---------------- DELETE COMPLAINT ----------------
@app.route('/delete_complaint/<int:complaint_id>')
def delete_complaint(complaint_id):
    cursor.execute("""
        DELETE FROM helpdesk 
        WHERE complaint_id=? AND status='resolved'
    """, (complaint_id,))
    db.commit()
    return redirect('/warden')


# ---------------- RESOLVE ----------------
@app.route('/resolve/<int:complaint_id>')
def resolve_complaint(complaint_id):
    if 'user' not in session:
        return redirect('/')

    cursor.execute("UPDATE helpdesk SET status='resolved' WHERE complaint_id=?", (complaint_id,))
    db.commit()

    if session.get('role') == 'worker':
        return redirect('/worker')
    return redirect('/warden')


# ---------------- WARDEN ----------------
@app.route('/warden')
def warden():
    if 'user' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM helpdesk")
    complaints = cursor.fetchall()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM workers")
    workers = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM helpdesk")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM helpdesk WHERE status='pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM helpdesk WHERE status='resolved'")
    resolved = cursor.fetchone()[0]

    return render_template('warden_dashboard.html',
                           complaints=complaints,
                           students=students,
                           workers=workers,
                           total=total,
                           pending=pending,
                           resolved=resolved)


# ---------------- WORKER ----------------
@app.route('/worker')
def worker():
    if 'user' not in session:
        return redirect('/')

    worker_id = session['user']

    cursor.execute("""
        SELECT * FROM helpdesk 
        WHERE status='pending' AND worker_id=?
    """, (worker_id,))

    data = cursor.fetchall()

    return render_template('worker_dashboard.html', data=data)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- RUN ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)