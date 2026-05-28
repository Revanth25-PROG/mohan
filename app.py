import os
import psycopg2
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    g
)

# Load environment variables
load_dotenv()
if not os.environ.get("DB_HOST"):
    load_dotenv("req.env")

# =========================
# FLASK APP
# =========================

app = Flask(__name__)

# =========================
# SUPABASE CONNECTION
# =========================

def get_db():
    if 'db' not in g:
        db_host = os.environ.get("DB_HOST", "db.dwunumnikuafvlgcgrnw.supabase.co")
        db_name = os.environ.get("DB_NAME", "postgres")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "REVANTH@206")
        db_port = os.environ.get("DB_PORT", "5432")
        g.db = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
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
    with db.cursor() as cur:
        cur.execute("""

            SELECT *

            FROM admin

            WHERE username=%s
            AND password=%s

        """, (username, password))

        admin = cur.fetchone()

    if admin:

        return redirect('/board')

    else:

        return "Invalid Username or Password"

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
    with db.cursor() as cur:
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

    db.commit()

    return "Complaint Submitted Successfully"

# =========================
# DASHBOARD PAGE
# =========================

@app.route('/board')
def board():

    return render_template("board.html")

# =========================
# GET COUNTS
# =========================

@app.route('/get_counts')
def get_counts():

    db = get_db()
    with db.cursor() as cur:
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
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM complaints"
        )

        complaints = cur.fetchall()

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
    with db.cursor() as cur:
        cur.execute("""

            SELECT COUNT(*)

            FROM complaints

            WHERE status='Solved'

        """)

        completed_count = cur.fetchone()[0]

        cur.execute("""

            SELECT *

            FROM complaints

            WHERE status='Solved'

        """)

        complaints = cur.fetchall()

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
        with db.cursor() as cur:
            cur.execute("""

                SELECT *

                FROM complaints

                WHERE name=%s

            """, (name,))

            complaints = cur.fetchall()

    return render_template(

        "user.html",

        complaints=complaints

    )

# =========================
# SOLVE COMPLAINT
# =========================

@app.route('/solve/<int:id>')
def solve(id):

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""

            UPDATE complaints

            SET status='Solved'

            WHERE id=%s

        """, (id,))

    db.commit()

    return redirect('/details')

# =========================
# RUN FLASK
# =========================

if __name__ == "__main__":

    app.run(

        debug=True,

        host='0.0.0.0',

        port=5000

    )