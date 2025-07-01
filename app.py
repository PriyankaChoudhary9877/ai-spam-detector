from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pickle
import datetime
import csv
import io
import os
import psycopg2

# Securely get password from environment variable
DB_PASSWORD = os.environ["SUPABASE_DB_PASSWORD"]


def get_connection():
    return psycopg2.connect(
        host="aws-0-ap-south-1.pooler.supabase.com",
        port="5432",
        dbname="postgres",
        user="postgres.pybqaiwoijmxpikyyvty",
        password=DB_PASSWORD
    )

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

# Load your model and vectorizer
model = pickle.load(open("spam_model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# Redirect root to login
@app.route('/')
def root():
    return redirect(url_for('login'))

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                return render_template("register.html", error="Username already exists.")
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        conn.close()
        return render_template("register.html", message="Registration successful! Please login.")
    return render_template("register.html")

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Home (Spam Detector)
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    prediction = None
    if request.method == 'POST':
        message = request.form['message']
        data = vectorizer.transform([message])
        pred = model.predict(data)[0]
        prediction = "Spam" if pred == 1 else "Not Spam"

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO emails (text, prediction, timestamp,user_id) VALUES (%s, %s, %s,%s)",
                (message, prediction, datetime.datetime.now(),session['user'])
            )
            conn.commit()
        conn.close()

    return render_template("index.html", prediction=prediction)

# Admin History
@app.route('/admin-history')
def admin_history():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM emails ORDER BY timestamp DESC")
        columns = [desc[0] for desc in cursor.description]
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()

    return render_template("admin.html", records=records)

# Download CSV
@app.route('/download-history')
def download_history():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, text, prediction, timestamp FROM emails ORDER BY timestamp DESC")
        rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Text', 'Prediction', 'Timestamp'])
    for row in rows:
        writer.writerow(row)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        download_name='prediction_history.csv',
        as_attachment=True
    )

# Feedback
@app.route('/feedback', methods=['POST'])
def feedback():
    if 'user' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO feedback (name, email, message, timestamp) VALUES (%s, %s, %s, %s)",
            (name, email, message, datetime.datetime.now())
        )
        conn.commit()
    conn.close()

    return render_template("index.html", prediction=None, feedback_msg="Thank you for your feedback!")

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
