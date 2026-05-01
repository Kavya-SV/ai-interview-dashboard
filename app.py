from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import Flask, render_template, request
import PyPDF2
import uuid
import time
import smtplib
from email.mime.text import MIMEText
from utils.resume_parser import extract_skills
from utils.question_generator import generate_questions
from utils.evaluator import evaluate_answer
from database.db import get_db
from flask import redirect
from flask import session
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import send_file

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template("index.html")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/signup')
        return f(*args,**kwargs)
    return wrapper
def send_otp(email,otp):
    sender="interviewhireiq.ai@gmail.com"
    app_password=os.getenv("APP_PASSWORD")

    msg= MIMEText(f"""From InterviewHireIQ Website
                  \nYour OTP is: {otp}""")
    msg['Subject']="Password Reset OTP"
    msg['From']= sender
    msg['To']= email

    server=smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, app_password)
    server.send_message(msg)
    server.quit()
@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if not session['is_admin']:
        return "Unauthorized"
    
    cursor.execute("SELECT id, user_id, uploaded_at FROM resumes")
    data = cursor.fetchall()

    conn.close()

    return render_template("admin.html", data=data)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_SIZE=50 * 1024* 1024

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    file = request.files['resume']
    role = request.form['role']

    if not allowed_file(file.filename):
        return "Only PDF allowed"
    
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_SIZE:
        return "File size exceeded (Max: 50MB)"
    
    filename = str(uuid.uuid4()) + ".pdf"
    path = os.path.join("uploads", filename)
    file.save(path)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resumes (user_id, file_path) VALUES (%s, %s)",
        (session['user_id'], path)
    )
    conn.commit()
    conn.close()

    if file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""

        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

        skills = extract_skills(text)

        questions = generate_questions(skills, role)

        return render_template(
            "result.html",
            skills=skills,
            questions=questions,
            text=text,
            role=role
        )

    return "No file uploaded"

@app.route('/signup',methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    hashed = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return f"""
            Username already exists.<br>
            Try:<br>
            {username}_0619<br>
            {username}_13<br>
            {username}_969<br>
            {username}_09
        """

    # check email
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return "Email already exists"

    # insert user
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, hashed)
    )

    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/view_resume/<int:id>')
@login_required
def view_resume(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if session.get('is_admin'):
        cursor.execute(
            "SELECT file_path FROM resumes WHERE id=%s",
            (id,)
        )
    else:
        cursor.execute(
            "SELECT file_path FROM resumes WHERE id=%s AND user_id=%s",
            (id, session['user_id'])
        )

    data = cursor.fetchone()
    conn.close()

    if not data:
        return "Unauthorized"

    UPLOAD_FOLDER = os.path.abspath("uploads")

    return send_file(os.path.join(UPLOAD_FOLDER, os.path.basename(data['file_path'])))
@app.route('/login', methods=['POST'])
def login():
    username=request.form['username']
    password=request.form['password']

    conn=get_db()
    cursor=conn.cursor(dictionary=True)

    cursor.execute("SELECT * from users WHERE username=%s",(username,))
    user=cursor.fetchone()


    if user and check_password_hash(user['password_hash'],password):
        session['user_id']=user['id']
        session['username'] = user['username']

        if not user['is_admin']:
            session['is_admin'] = False
        else:
            session['is_admin'] = True
        return redirect('/dashboard')
    return "Invalid credentials"

@app.route('/history')
@login_required
def history():
    conn=get_db()
    cursor=conn.cursor(dictionary=True)

    cursor.execute(""" SELECT id,user_id,question,answer,score, feedback, created_at FROM attemts
                   WHERE user_id=%s ORDER BY created_at DESC""",(session['user_id'],))
    
    data=cursor.fetchall()
    conn.close()

    return render_template("history.html", data=data)
@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    text=request.form['text']
    question=request.form['q']
    answer = request.form['answer']
    role = request.form['role']

    score, feedback = evaluate_answer(role, text, question, answer)

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("INSERT INTO attemts (user_id, role, question, answer, score, feedback) VALUES (%s,%s,%s,%s,%s,%s)",(session['user_id'], role, question, answer, score, feedback))

    conn.commit()
    conn.close()

    return f"{feedback}"

@app.route('/forgot')
def forgot():
    return render_template("forgot.html")

@app.route('/reset', methods=['POST'])
def reset():
    email=request.form['email']
    conn=get_db()
    cursor=conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
    valid=cursor.fetchone()

    conn.close()
    cursor.close()
    if not valid:
        return "Email not found"
    import random
    otp=str(random.randint(100000, 999999))

    session['otp']=otp
    session['email']=email
    session['otp_attempts'] = 0        
    session['otp_time'] = time.time()

    send_otp(email, otp)
    return redirect('/verify')
@app.route('/verify')
def verify_page():
    return render_template("otp.html")

@app.route('/verify', methods=['POST'])
def verify():
    otp = request.form['otp']

    if time.time() - session.get('otp_time', 0) > 300:
        return "OTP expired"

    if otp == session.get('otp'):
        session.pop('otp_attempts', None)
        session.pop('otp_time', None)
        return render_template("reset.html")

    session['otp_attempts'] = session.get('otp_attempts', 0) + 1

    if session['otp_attempts'] > 3:
        session['otp']=None
        return "Too many attempts"

    remaining = 3 - session['otp_attempts']
    return f"Invalid OTP. {remaining} attempts left"
@app.route('/new_password', methods=['POST'])
def new_password():
    key=request.form['password']
    re_pass=request.form['repassword']
    if key!=re_pass:
        return "Password doesn't match"
    hashed=generate_password_hash(key)

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("UPDATE users SET password_hash=%s WHERE email=%s",(hashed, session['email']))

    conn.commit()
    conn.close()

    return redirect('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id = session.get('user_id')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attemts WHERE user_id=%s", (user_id,))
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

    conn.commit()
    conn.close()

    session.clear()

    return redirect('/')
@app.route('/delete_attempts', methods=['POST'])
@login_required
def delete_attempts():
    user_id = session.get('user_id')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attemts WHERE user_id=%s", (user_id,))

    conn.commit()
    conn.close()
    return redirect('/')
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect('/')
if __name__ == '__main__':
    app.run()