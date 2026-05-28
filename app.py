import os
import ssl
import pg8000.dbapi
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    g,
    session,
    url_for
)

# Load environment variables
load_dotenv()
if not os.environ.get("DB_HOST"):
    load_dotenv("req.env")

# =========================
# FLASK APP
# =========================

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "smart_community_secret_key_9876")

import traceback

@app.errorhandler(500)
def handle_500(e):
    return f"<h1>Internal Server Error (500)</h1><pre>{traceback.format_exc()}</pre>", 500

@app.errorhandler(Exception)
def handle_exception(e):
    return f"<h1>Unhandled Exception</h1><pre>{traceback.format_exc()}</pre>", 500

# =========================
# SUPABASE CONNECTION
# =========================

def get_db():
    if 'db' not in g:
        db_host = os.environ.get("DB_HOST", "db.dwunumnikuafvlgcgrnw.supabase.co")
        db_name = os.environ.get("DB_NAME", "postgres")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "REVANTH@206")
        db_port = int(os.environ.get("DB_PORT", "5432"))
        
        # Enforce SSL context for secure connection in serverless environment
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        g.db = pg8000.dbapi.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
            ssl_context=ssl_context
        )
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


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
# ADMIN LOGIN CHECK
# =========================

@app.route('/adminlogin', methods=['POST'])
def adminlogin():

    username = request.form['username']

    password = request.form['password']

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""

            SELECT *

            FROM admin

            WHERE username=%s
            AND password=%s

        """, (username, password))

        admin = cur.fetchone()
    finally:
        cur.close()

    if admin:
        session['admin_id'] = admin[0]
        session['admin_username'] = admin[1]
        return redirect('/board')

    else:

        return "Invalid Username or Password"

# =========================
# ADMIN LOGOUT
# =========================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =========================
# HOME PAGE
# =========================

@app.route('/home')
def home():

    return render_template("home.html")

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

    db = get_db()
    cur = db.cursor()
    try:
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
    finally:
        cur.close()

    db.commit()

    return render_template("success.html", message="Complaint Submitted Successfully")

# =========================
# DASHBOARD PAGE
# =========================

@app.route('/board')
def board():
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT 
                c.id, c.name, c.phone, c.complaint_type, c.location, 
                c.description, c.status, c.image, a.username 
            FROM complaints c
            LEFT JOIN admin a ON c.resolved_by = a.id
            ORDER BY c.id DESC
        """)
        complaints = cur.fetchall()
    finally:
        cur.close()
    return render_template("board.html", complaints=complaints)

# =========================
# GET COUNTS
# =========================

@app.route('/get_counts')
def get_counts():

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "SELECT COUNT(*) FROM complaints"
        )

        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM complaints WHERE status='Pending'"
        )

        pending = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM complaints WHERE status='Solved'"
        )

        solved = cur.fetchone()[0]
    finally:
        cur.close()

    return jsonify({

        "total": total,

        "pending": pending,

        "solved": solved

    })

# =========================
# SHOW ALL COMPLAINTS
# =========================

@app.route('/details')
def details():

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT 
                c.id, c.name, c.phone, c.complaint_type, c.location, 
                c.description, c.status, c.image, a.username 
            FROM complaints c
            LEFT JOIN admin a ON c.resolved_by = a.id
            ORDER BY c.id DESC
        """)

        complaints = cur.fetchall()
    finally:
        cur.close()

    return render_template(

        "details.html",

        complaints=complaints

    )

# =========================
# COMPLETED COMPLAINTS
# =========================

@app.route('/completed')
def completed():

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""

            SELECT COUNT(*)

            FROM complaints

            WHERE status='Solved'

        """)

        completed_count = cur.fetchone()[0]

        cur.execute("""

            SELECT 
                c.id, c.name, c.phone, c.complaint_type, c.location, 
                c.description, c.status, c.image, a.username 
            FROM complaints c
            LEFT JOIN admin a ON c.resolved_by = a.id
            WHERE c.status='Solved'
            ORDER BY c.id DESC

        """)

        complaints = cur.fetchall()
    finally:
        cur.close()

    return render_template(

        "completed.html",

        complaints=complaints,

        completed_count=completed_count

    )

# =========================
# USER SEARCH
# =========================

@app.route('/user', methods=['GET', 'POST'])
def user():

    complaints = None

    if request.method == 'POST':

        name = request.form['name']

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""

                SELECT 
                    c.id, c.name, c.phone, c.complaint_type, c.location, 
                    c.description, c.status, c.image, a.username 
                FROM complaints c
                LEFT JOIN admin a ON c.resolved_by = a.id
                WHERE c.name=%s
                ORDER BY c.id DESC

            """, (name,))

            complaints = cur.fetchall()
        finally:
            cur.close()

    return render_template(

        "user.html",

        complaints=complaints

    )

# =========================
# SOLVE COMPLAINT (GET)
# =========================

@app.route('/solve/<int:id>')
def solve(id):

    admin_id = session.get('admin_id', 1)
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""

            UPDATE complaints

            SET status='Solved', resolved_by=%s

            WHERE id=%s

        """, (admin_id, id))
    finally:
        cur.close()

    db.commit()

    return redirect('/details')

# =========================
# COMPLETE COMPLAINT (POST)
# =========================

@app.route('/completed/<int:id>', methods=['POST'])
def complete_complaint(id):

    admin_id = session.get('admin_id', 1)
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""

            UPDATE complaints

            SET status='Solved', resolved_by=%s

            WHERE id=%s

        """, (admin_id, id))
    finally:
        cur.close()

    db.commit()

    return redirect('/board')

# =========================
# RUN FLASK
# =========================

if __name__ == "__main__":

    app.run(

        debug=True,

        host='0.0.0.0',

        port=5000

    )