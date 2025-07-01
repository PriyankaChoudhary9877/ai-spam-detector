from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pickle
import pymysql
import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

# Load model & vectorizer
model = pickle.load(open("spam_model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# Database config
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'systemelvish',
    'database': 'spamdb'
}

# 🔁 Redirect root to login
@app.route('/')
def root():
    return redirect(url_for('login'))

# 📝 Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                return render_template("register.html", error="Username already exists.")
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        conn.close()
        return render_template("register.html", message="Registration successful! Please login.")
    return render_template("register.html")

# 🔐 Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = pymysql.connect(**db_config)
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

# 🚪 Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# 🏠 Home (Spam Detector)
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

        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO emails (text, prediction, timestamp) VALUES (%s, %s, %s)",
                           (message, prediction, datetime.datetime.now()))
            conn.commit()
        conn.close()

    return render_template("index.html", prediction=prediction)

# 📊 Admin History
@app.route('/admin-history')
def admin_history():
    # Allow only admin to access
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    conn = pymysql.connect(**db_config)
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM emails ORDER BY timestamp DESC")
        records = cursor.fetchall()
    conn.close()
    return render_template("admin.html", records=records)


# 📥 Download CSV
@app.route('/download-history')
def download_history():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = pymysql.connect(**db_config)
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
@app.route('/feedback', methods=['POST'])
def feedback():
    if 'user' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    conn = pymysql.connect(**db_config)
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO feedback (name, email, message, timestamp) VALUES (%s, %s, %s, %s)",
            (name, email, message, datetime.datetime.now())
        )
        conn.commit()
    conn.close()

    return render_template("index.html", prediction=None, feedback_msg="Thank you for your feedback!")


if __name__ == '__main__':
    app.run(debug=True)
