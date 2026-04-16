# 🏨 Hostel Management System

A full-stack web application designed to manage hostel operations including student registration, complaint handling, and worker assignment.

---

## 🚀 Live Demo

👉 https://hostel-management-system-1-9pie.onrender.com

---

## 📌 Features

### 👨‍🎓 Student
- Register and login
- Raise complaints (Water, Electricity, WiFi, Cleaning)
- View complaint status (Pending / Resolved)

### 👨‍💼 Warden
- Login using demo credentials
- Add / Delete Students
- Add / Delete Workers
- View all complaints
- Assign workers to complaints
- Resolve complaints

### 🛠 Worker
- Login
- View assigned complaints
- Mark complaints as completed

---

## 🛠 Tech Stack

- **Frontend:** HTML, CSS, Bootstrap  
- **Backend:** Flask (Python)  
- **Database:** SQLite  
- **Deployment:** Render  

---

## 🗄 Database Tables

- **Students** → student_id, name, phone, room_no, password  
- **Workers** → worker_id, name, password  
- **Wardens** → warden_id, password  
- **Complaints (Helpdesk)** → complaint_id, issue_type, room_no, student_id, status, worker_id  

---

## 🔐 Demo Login

Warden Login
ID: 1
Password: 123
---

## ⚙️ Installation (Run Locally)

```bash
git clone https://github.com/your-username/hostel-management-system.git
cd hostel-management-system/backend
pip install -r requirements.txt
python app.py

Project Structure
Hostel_management/
│
├── backend/
│   ├── app.py
│   ├── templates/
│   ├── static/
│
├── database/
│   └── schema.sql
│
├── .gitignore
└── README.md

Future Improvements
Implement password encryption for all users using hashing techniques
Add email notifications for complaint updates and status changes
Improve UI/UX with modern design and better user experience
Implement role-based authentication and access control
Add analytics dashboard for complaint statistics
Real-time updates for complaint status

Authors
Harshitha Vandavasi
Dattu Nayak

Note
This project is developed for academic and learning purposes.

