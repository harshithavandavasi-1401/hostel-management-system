from flask import Flask, render_template, request, redirect, session
import os
import mysql.connector
import bcrypt

# ---------------- PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = "secret123"

# ---------------- DB ----------------
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Harshitha@2006",
    database="hostel_db",
    auth_plugin='mysql_native_password'
)
cursor = db.cursor()

print("✅ Connected to MySQL")

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
        cursor.execute("SELECT * FROM students WHERE student_id=%s", (user_id,))
        user = cursor.fetchone()

        if user:
            stored_password = user[7]
            if isinstance(stored_password, str):
                stored_password = stored_password.encode()

            if bcrypt.checkpw(password.encode(), stored_password):
                session['user'] = user_id
                session['role'] = 'student'
                return redirect('/student')

    elif role == 'warden':
        cursor.execute("SELECT * FROM wardens WHERE warden_id=%s AND password=%s", (user_id, password))
        if cursor.fetchone():
            session['user'] = user_id
            session['role'] = 'warden'
            return redirect('/warden')

    elif role == 'worker':
        cursor.execute("SELECT * FROM workers WHERE worker_id=%s AND password=%s", (user_id, password))
        if cursor.fetchone():
            session['user'] = user_id
            session['role'] = 'worker'
            return redirect('/worker')

    return "❌ Invalid Login"


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        reg = request.form['reg']
        phone = request.form['phone']
        room = request.form['room']
        password = request.form['password']

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO students (student_id, name, phone, room_no, password)
            VALUES (%s, %s, %s, %s, %s)
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

    cursor.execute("SELECT name, room_no FROM students WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM helpdesk WHERE student_id=%s", (student_id,))
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

    cursor.execute("SELECT room_no FROM students WHERE student_id=%s", (student_id,))
    room_no = cursor.fetchone()[0]

    student_name = request.form['student_name']
    issue_type = request.form['issue_type']

    cursor.execute("""
        INSERT INTO helpdesk 
        (issue_type, description, room_no, student_id, student_name, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (issue_type, "", room_no, student_id, student_name, "pending"))

    db.commit()
    return redirect('/student')


# ---------------- RESOLVE ----------------
@app.route('/resolve/<int:complaint_id>')
def resolve_complaint(complaint_id):
    if 'user' not in session:
        return redirect('/')

    cursor.execute("UPDATE helpdesk SET status='resolved' WHERE complaint_id=%s", (complaint_id,))
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


# ---------------- ASSIGN WORKER ----------------
@app.route('/assign_worker', methods=['POST'])
def assign_worker():
    complaint_id = request.form['complaint_id']
    worker_id = request.form['worker_id']

    cursor.execute("""
        UPDATE helpdesk SET worker_id=%s 
        WHERE complaint_id=%s
    """, (worker_id, complaint_id))

    db.commit()
    return redirect('/warden')


# ---------------- ADD WORKER ----------------
@app.route('/add_worker', methods=['POST'])
def add_worker():
    name = request.form['name']
    password = request.form['password']

    cursor.execute("""
        INSERT INTO workers (name, password)
        VALUES (%s, %s)
    """, (name, password))

    db.commit()
    return redirect('/warden')


# ---------------- DELETE WORKER ----------------
@app.route('/delete_worker/<int:worker_id>')
def delete_worker(worker_id):
    cursor.execute("DELETE FROM workers WHERE worker_id=%s", (worker_id,))
    db.commit()
    return redirect('/warden')


# ---------------- ADD STUDENT ----------------
@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    reg = request.form['reg']
    phone = request.form['phone']
    father = request.form['father']
    room = request.form['room']

    cursor.execute("""
        INSERT INTO students (student_id, name, phone, father_name, room_no)
        VALUES (%s, %s, %s, %s, %s)
    """, (reg, name, phone, father, room))

    db.commit()
    return redirect('/warden')


# ---------------- DELETE STUDENT ----------------
@app.route('/delete_student/<student_id>')
def delete_student(student_id):
    cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
    db.commit()
    return redirect('/warden')


# ---------------- WORKER ----------------
@app.route('/worker')
def worker():
    if 'user' not in session:
        return redirect('/')

    worker_id = session['user']

    cursor.execute("""
        SELECT * FROM helpdesk 
        WHERE status='pending' AND worker_id=%s
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
    app.run(debug=True, host="0.0.0.0", port=5001)