import ast
import json
import sqlite3
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import asynccontextmanager
from fastapi import Form, FastAPI, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from hackerrank_main import HRMain
from hackerrank_plagiarismCheck import plagiariseCodes
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Initialize app directories
templates = Jinja2Templates(directory="templates")
DATABASE = 'users.db'
RESET_TOKENS = {}

# Use environment variables for sensitive info
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))


# ----------------------- Helper Functions -----------------------
def set_flash(request: Request, message: str, category: str = "info"):
    request.session["flash"] = {"message": message, "category": category}

def get_flash(request: Request):
    flash = request.session.pop("flash", None)
    return flash

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# ----------------------- FastAPI Lifespan -----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ Database initialized successfully!")
    yield
    print("🛑 Application shutting down...")


# ----------------------- App Configuration -----------------------
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="dhsbjjdjsjdjsnj1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------- Routes -----------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    flash = get_flash(request)
    return templates.TemplateResponse("login.html", {"request": request, "flash": flash})

@app.post("/login")
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        set_flash(request, "Logged in successfully!", "success")
        return RedirectResponse(url="/index", status_code=303)
    else:
        set_flash(request, "Incorrect email or password!", "danger")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    hashed_password = generate_password_hash(password)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
        conn.commit()
        set_flash(request, "Account created successfully!", "success")
        return RedirectResponse(url="/login", status_code=303)
    except sqlite3.IntegrityError:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username or Email already exists"})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password")
async def forgot_password_post(request: Request, email: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if user:
        token = str(uuid.uuid4())
        RESET_TOKENS[token] = user['email']

        reset_link = f"http://127.0.0.1:8000/reset-password?token={token}"
        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = email
        message['Subject'] = "Password Reset Request"
        message.attach(MIMEText(f"Click the link to reset your password: {reset_link}", 'plain'))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, email, message.as_string())
            print(f"✅ Email sent to {email}")
            return templates.TemplateResponse("forgot_password.html", {"request": request, "message": "Password reset instructions sent to your email"})
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "Error sending email"})
    else:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "Email not found"})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password(request: Request, token: str):
    email = RESET_TOKENS.get(token)
    if email:
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})
    else:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Invalid or expired token"})

@app.post("/reset-password")
async def reset_password_post(request: Request, token: str = Form(...), password: str = Form(...)):
    email = RESET_TOKENS.pop(token, None)
    if email:
        hashed_password = generate_password_hash(password)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        return RedirectResponse(url="/login", status_code=303)
    else:
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid or expired token"})

@app.get("/index", response_class=HTMLResponse)
async def homePage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "data": {}})

@app.get("/fetchLatest/")
async def fetchLatest(request: Request):
    adminUsername = request.query_params.get("username")
    adminPassword = request.query_params.get("password")
    contest_slug = request.query_params.get("contestSlug")
    hr = HRMain(adminUsername, adminPassword, contest_slug)
    data = hr.fetchData()
    return templates.TemplateResponse("index.html", {"request": request, "data": data})

@app.get("/fetchOld/")
async def fetchOld(request: Request):
    adminUsername = request.query_params.get("username")
    adminPassword = request.query_params.get("password")
    contest_slug = request.query_params.get("contestSlug")
    hr = HRMain(adminUsername, adminPassword, contest_slug)
    data = hr.fetchOldData()
    return templates.TemplateResponse("userAttempts.html", {"request": request, "data": data})

@app.get("/plagiariseCode/")
async def plagiarise_code(request: Request, userData: str = Query(...)):
    try:
        userData = ast.literal_eval(userData)
    except (ValueError, SyntaxError) as e:
        return {"error": f"Invalid userData format: {str(e)}"}
    res = plagiariseCodes(userData)
    return templates.TemplateResponse("result.html", {"request": request, "res": res})
