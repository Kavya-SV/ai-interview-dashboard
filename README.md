#  AI-Powered Resume Analysis & Interview Preparation Platform

A full-stack web application that analyzes resumes and generates role-based interview questions using AI-driven logic. The platform supports secure authentication, cloud storage, and real-time processing.

---

## 🌐 Live Demo
👉 https://ai-interview-dashboard-xiah.onrender.com/

---

##  Features

-  Upload resumes (PDF only) with validation and size limits  
-  Store resumes securely using AWS S3 (persistent cloud storage)  
-  Extract text and identify key skills using PyPDF2  
-  Generate dynamic interview questions based on skills and selected role  
-  Secure authentication with session management (user/admin roles)  
-  OTP-based password reset using SendGrid  
-  Admin dashboard to view and manage all uploaded resumes  
-  Deployed and accessible online via Render  

---

##  Tech Stack

- **Backend:** Python, Flask  
- **Frontend:** HTML, CSS, Jinja2  
- **Database:** MySQL  
- **Cloud Storage:** AWS S3 (boto3)  
- **Email Service:** SendGrid  
- **PDF Processing:** PyPDF2  
- **Deployment:** Render  

---

## ⚙️ Installation (Run Locally)

```bash
git clone https://github.com/Kavya-SV/ai-interview-dashboard.git
cd ai-interview-dashboard

pip install -r requirements.txt
python app.py
