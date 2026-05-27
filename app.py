import os
from flask import Flask, render_template, request, redirect, jsonify
import mysql.connector

app = Flask(__name__)

# =========================
# MYSQL CONNECTION
# =========================

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "complaint_system")
    )

conn = get_connection()
cur = conn.cursor()

# =========================
# WELCOME PAGE
# =========================

@app.route('/')
def welcome():
    return render_template("welcome.html")

# =========================
# ADMIN LOGIN PAGE
# =========================
@app.route('/admin')
def admin():
    return render_template("login.html")
# =========================
# HOME PAGE
# =========================

@app.route('/home')
def home():
    return render_template("home.html")

# =========================
# ADMIN LOGIN CHECK
# =========================

@app.route('/adminlogin', methods=['POST'])
def adminlogin():

    username = request.form['username']
    password = request.form['password']

    cur.execute("""
        SELECT * FROM admin
        WHERE username=%s AND password=%s
    """, (username, password))

    admin = cur.fetchone()

    if admin:
        return render_template("admin.html")
    else:
        return "Invalid Username or Password"

# =========================
# COMPLAINT FORM PAGE
# =========================

@app.route('/form')
def form():
    return render_template("form.html")

# =========================
# SUBMIT COMPLAINT
# =========================

@app.route('/submit', methods=['POST'])
def submit():

    name = request.form['name']
    phone = request.form['phone']
    complaint_type = request.form['complaint_type']
    location = request.form['location']
    description = request.form['description']

    cur.execute("""
        INSERT INTO complaints(
            name,
            phone,
            complaint_type,
            location,
            description,
            status
        )
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (
        name,
        phone,
        complaint_type,
        location,
        description,
        "Pending"
    ))

    conn.commit()

    return "Complaint Submitted Successfully"

# =========================
# RUN FLASK
# =========================
@app.route('/board')
def board():
    return render_template("board.html")

@app.route('/get_counts')
def get_counts():

    cur.execute("SELECT COUNT(*) FROM complaints")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Pending'"
    )
    pending = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Solved'"
    )
    solved = cur.fetchone()[0]

    return jsonify({
        "total": total,
        "pending": pending,
        "solved": solved
    })
@app.route('/details')
def details():

    cur.execute("SELECT * FROM complaints")

    complaints = cur.fetchall()

    return render_template(
        "details.html",
        complaints=complaints
    )
@app.route('/completed')
def completed():

    cur.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Solved'"
    )

    completed_count = cur.fetchone()[0]

    cur.execute(
        "SELECT * FROM complaints WHERE status='Solved'"
    )

    complaints = cur.fetchall()

    return render_template(
        "completed.html",
        complaints=complaints,
        completed_count=completed_count
    )
from flask import Flask, render_template, request

@app.route('/user', methods=['GET', 'POST'])
def search():

    complaints = []

    if request.method == 'POST':

        name = request.form['name']

        cur.execute(
            "SELECT * FROM complaints WHERE name=%s",(name,) 
        )

        complaints = cur.fetchall()

    return render_template(
        "user.html",
        complaints=complaints
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)