# from flask import Flask, render_template, request, redirect, url_for, session, send_file
# import pickle
# import datetime
# import csv
# import io
# import os
# import psycopg2


# DB_PASSWORD = os.environ["SUPABASE_DB_PASSWORD"]


# def get_connection():
#     return psycopg2.connect(
#         host="aws-0-ap-south-1.pooler.supabase.com",
#         port="5432",
#         dbname="postgres",
#         user="postgres.pybqaiwoijmxpikyyvty",
#         password=DB_PASSWORD
#     )

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # For session management

# # Load model and vectorizer
# model = pickle.load(open("spam_model.pkl", "rb"))
# vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# # Redirect root to login
# @app.route('/')
# def root():
#     return redirect(url_for('login'))

# # Register Page
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         conn = get_connection()
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
#             if cursor.fetchone():
#                 return render_template("register.html", error="Username already exists.")
#             cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
#             conn.commit()
#         conn.close()
#         return render_template("register.html", message="Registration successful! Please login.")
#     return render_template("register.html")

# # Login Page
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         conn = get_connection()
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
#             user = cursor.fetchone()
#         conn.close()

#         if user:
#             session['user'] = username
#             return redirect(url_for('home'))
#         else:
#             return render_template('login.html', error="Invalid credentials.")
#     return render_template('login.html')

# # Logout
# @app.route('/logout')
# def logout():
#     session.pop('user', None)
#     return redirect(url_for('login'))

# # Home (Spam Detector)
# @app.route('/home', methods=['GET', 'POST'])
# def home():
#     if 'user' not in session:
#         return redirect(url_for('login'))

#     prediction = None
#     if request.method == 'POST':
#         message = request.form['message']
#         data = vectorizer.transform([message])
#         pred = model.predict(data)[0]
#         prediction = "Spam" if pred == 1 else "Not Spam"

#         conn = get_connection()
#         with conn.cursor() as cursor:
#             cursor.execute(
#                 "INSERT INTO emails (text, prediction, timestamp,user_id) VALUES (%s, %s, %s,%s)",
#                 (message, prediction, datetime.datetime.now(),session['user'])
#             )
#             conn.commit()
#         conn.close()

#     return render_template("index.html", prediction=prediction)

# # Admin History
# @app.route('/admin-history')
# def admin_history():
#     if 'user' not in session or session['user'] != 'admin':
#         return redirect(url_for('login'))

#     conn = get_connection()
#     with conn.cursor() as cursor:
#         cursor.execute("SELECT * FROM emails ORDER BY timestamp DESC")
#         columns = [desc[0] for desc in cursor.description]
#         records = [dict(zip(columns, row)) for row in cursor.fetchall()]
#     conn.close()

#     return render_template("admin.html", records=records)

# # Download CSV
# @app.route('/download-history')
# def download_history():
#     if 'user' not in session:
#         return redirect(url_for('login'))

#     conn = get_connection()
#     with conn.cursor() as cursor:
#         cursor.execute("SELECT id, text, prediction, timestamp FROM emails ORDER BY timestamp DESC")
#         rows = cursor.fetchall()
#     conn.close()

#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(['ID', 'Text', 'Prediction', 'Timestamp'])
#     for row in rows:
#         writer.writerow(row)
#     output.seek(0)

#     return send_file(
#         io.BytesIO(output.getvalue().encode()),
#         mimetype='text/csv',
#         download_name='prediction_history.csv',
#         as_attachment=True
#     )

# # Feedback
# @app.route('/feedback', methods=['POST'])
# def feedback():
#     if 'user' not in session:
#         return redirect(url_for('login'))

#     name = request.form['name']
#     email = request.form['email']
#     message = request.form['message']

#     conn = get_connection()
#     with conn.cursor() as cursor:
#         cursor.execute(
#             "INSERT INTO feedback (name, email, message, timestamp) VALUES (%s, %s, %s, %s)",
#             (name, email, message, datetime.datetime.now())
#         )
#         conn.commit()
#     conn.close()

#     return render_template("index.html", prediction=None, feedback_msg="Thank you for your feedback!")

# # Run the app
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host='0.0.0.0', port=port)
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pickle
import datetime
import csv
import io
import os
import psycopg2
from gmail_auth import get_gmail_service  #gmail email fetch function



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

# Load model and vectorizer
model = pickle.load(open("spam_model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# email
def get_recent_emails():
    service = get_gmail_service() #to authenticate and create a Gmail API client.
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])
    email_list = []

# userId='me' tells the API to use the currently authenticated user.
# execute() sends the API request.
# messages will contain a list of messages (each with an id).

# For each email it sends a request to fetch full details using the id.
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload'].get('headers', []) 
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        snippet = msg_data.get('snippet', '') #email snippet=short preview of the message
        email_list.append({'id': msg['id'], 'subject': subject, 'snippet': snippet})

    return email_list



@app.route('/gmail_inbox')
def gmail_inbox():
    emails = get_recent_emails()  #call thr email fetcher
    return render_template('gmail_inbox.html', emails=emails)


@app.route('/check-spam', methods=['POST'])
def check_spam():
    if 'user' not in session:
        return redirect(url_for('login'))

    message = request.form['message']
    vectorized = vectorizer.transform([message])
    prediction = model.predict(vectorized)[0]
    result = 'Spam' if prediction == 1 else 'Not Spam'
    
    return render_template('index.html', prediction=result, message=message, username=session['user'])


# Redirect root to login
@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Restrict reserved usernames (case-insensitive)
        reserved = ['priyanka', 'admin']
        if username.lower() in reserved:
            return render_template("register.html", error="This username is reserved and cannot be used.")

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
            print("✅ Logged in as:", session['user']) 
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
# @app.route('/home', methods=['GET', 'POST'])
# def home():
#     if 'user' not in session:
#         return redirect(url_for('login'))

#     prediction = None
#     if request.method == 'POST':
#         message = request.form['message']
#         data = vectorizer.transform([message])
#         pred = model.predict(data)[0]
#         prediction = "Spam" if pred == 1 else "Not Spam"

#         conn = get_connection()
#         with conn.cursor() as cursor:
#             cursor.execute(
#                 "INSERT INTO emails (text, prediction, timestamp,user_id) VALUES (%s, %s, %s,%s)",
#                 (message, prediction, datetime.datetime.now(),session['user'])
#             )
#             conn.commit()
#         conn.close()

#     return render_template("index.html", prediction=prediction)

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    prediction = None
    message = None

    if request.method == 'POST':
        message = request.form['message']
        data = vectorizer.transform([message])
        pred = model.predict(data)[0]
        prediction = "Spam" if pred == 1 else "Not Spam"

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO emails (text, prediction, timestamp, user_id) VALUES (%s, %s, %s, %s)",
                (message, prediction, datetime.datetime.now(), session['user'])
            )
            conn.commit()
        conn.close()

    return render_template("index.html", prediction=prediction, message=message, username=session['user'])
    



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

    return render_template("index.html", prediction=None, feedback_msg="Thank you for your feedback!", username=session['user'])


# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
