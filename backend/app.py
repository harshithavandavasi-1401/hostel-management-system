from flask import Flask, render_template, request, redirect, session
import sqlite3
import bcrypt
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
db = sqlite3.connect('hostel.db', check_same_thread=False)
cursor = db.cursor()
print("🔥 DB READY - SQLITE WORKING")

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
cursor.execute("INSERT OR IGNORE INTO wardens VALUES ('1','123')")
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
            stored_password = user[-1]

            try:
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode()

                if bcrypt.checkpw(password.encode(), stored_password):
                    session['user'] = user_id
                    session['role'] = 'student'
                    return redirect('/student')

            except:
                if password == stored_password:
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

    return render_template('login.html', error="Invalid credentials")


# ---------------- ADD STUDENT ----------------
@app.route('/add_student', methods=['POST'])
def add_student():
    cursor.execute("""
    INSERT INTO students (student_id, name, phone, room_no, password)
    VALUES (?, ?, ?, ?, ?)
    """, (
        request.form['student_id'],
        request.form['name'],
        request.form['phone'],
        request.form['room'],
        request.form['password']
    ))
    db.commit()
    return redirect('/warden')


# ---------------- ADD WORKER ----------------
@app.route('/add_worker', methods=['POST'])
def add_worker():
    cursor.execute("""
    INSERT INTO workers (worker_id, password)
    VALUES (?, ?)
    """, (
        request.form['worker_id'],
        request.form['password']
    ))
    db.commit()
    return redirect('/warden')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        hashed_password = bcrypt.hashpw(request.form['password'].encode(), bcrypt.gensalt())

        cursor.execute("""
        INSERT INTO students (student_id, name, phone, room_no, password)
        VALUES (?, ?, ?, ?, ?)
        """, (
            request.form['reg'],
            request.form['name'],
            request.form['phone'],
            request.form['room'],
            hashed_password
        ))

        db.commit()
        return redirect('/')

    return render_template('register.html')


# ---------------- STUDENT ----------------
@app.route('/student')
def student():
    if 'user' not in session:
        return redirect('/')

    sid = session['user']

    cursor.execute("SELECT name, room_no FROM students WHERE student_id=?", (sid,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM helpdesk WHERE student_id=?", (sid,))
    complaints = cursor.fetchall()

    return render_template('student_dashboard.html',
                           complaints=complaints,
                           student_name=student[0],
                           student_id=sid,
                           room_no=student[1])


# ---------------- SUBMIT ----------------
@app.route('/submit_complaint', methods=['POST'])
def submit():
    sid = session['user']

    cursor.execute("SELECT room_no FROM students WHERE student_id=?", (sid,))
    room = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO helpdesk (issue_type, description, room_no, student_id, student_name, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        request.form['issue_type'],
        "",
        room,
        sid,
        request.form['student_name'],
        "pending"
    ))

    db.commit()
    return redirect('/student')


# ---------------- WARDEN ----------------
@app.route('/warden')
def warden():
    cursor.execute("SELECT * FROM helpdesk")
    complaints = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM helpdesk")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM helpdesk WHERE status='pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM helpdesk WHERE status='resolved'")
    resolved = cursor.fetchone()[0]

    return render_template('warden_dashboard.html',
                           complaints=complaints,
                           total=total,
                           pending=pending,
                           resolved=resolved)


# ---------------- WORKER ----------------
@app.route('/worker')
def worker():
    cursor.execute("SELECT * FROM helpdesk WHERE status='pending'")
    data = cursor.fetchall()
    return render_template('worker_dashboard.html', data=data)


# ---------------- RESOLVE ----------------
@app.route('/resolve/<int:id>')
def resolve(id):
    cursor.execute("UPDATE helpdesk SET status='resolved' WHERE complaint_id=?", (id,))
    db.commit()
    return redirect('/warden')


# ---------------- DELETE ----------------
@app.route('/delete_complaint/<int:id>')
def delete(id):
    cursor.execute("DELETE FROM helpdesk WHERE complaint_id=? AND status='resolved'", (id,))
    db.commit()
    return redirect('/warden')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- RUN ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)