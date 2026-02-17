# hackerrank-automation-plagiarism
📌 Project Overview

HackerRank Automation Plagiarism Checker is a web-based tool that automatically collects contest submissions from HackerRank and checks code similarity between users to detect possible plagiarism.

The system uses Selenium automation, FastAPI backend, SQLite database, and Sentence Transformers (AI model) to compare source codes and generate plagiarism reports.

🚀 Features

Automated login to HackerRank using Selenium

Fetch latest contest submissions

Fetch previous (old) contest attempts

Store user attempts in SQLite database

AI-based plagiarism detection using Sentence Transformers

User Authentication (Signup / Login / Forgot Password)

Clean HTML dashboard for results

Source code similarity percentage calculation

Plagiarism report generation

🛠 Tech Stack

Frontend

HTML

CSS

Jinja2 Templates

Backend

Python

FastAPI

Selenium WebDriver

Database

SQLite3

AI / NLP

Sentence Transformers

PyTorch Cosine Similarity

Other Tools

Git & GitHub

Uvicorn Server

dotenv (.env)

📂 Project Structure
hackerrank-plagiarism-checker/
│
├── main.py
├── hackerrank_main.py
├── hackerrank_selenium.py
├── hackerrank_SQL.py
├── hackerrank_plagiarismCheck.py
│
├── templates/
├── static/
│
├── users.db
├── cookies.pkl
├── .env
└── requirements.txt

⚙️ Installation & Setup
1. Clone Repository
git clone https://github.com/your-username/hackerrank-automation-plagiarism.git
cd hackerrank-automation-plagiarism

2. Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows

3. Install Dependencies
pip install -r requirements.txt

4. Create .env File
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

5. Run Server
uvicorn main:app --reload


Open browser:

http://127.0.0.1:8000

🧠 How Plagiarism Detection Works

Fetch contest submissions using Selenium.

Store attempts in SQLite database.

Retrieve source codes.

Convert code into embeddings using Sentence Transformers.

Calculate similarity using cosine similarity.

If similarity > 95%, mark as potential plagiarism.

🔐 Security Notes

.env stores sensitive credentials.

cookies.pkl stores session cookies.

These files should not be pushed to GitHub.

Use .gitignore to exclude them.

📊 Example Output

Shows user name

Similar user

Problem slug

Programming language

Similarity score

Source code comparison

📈 Future Improvements

PostgreSQL / MySQL support

Admin dashboard

Real-time plagiarism alerts

Role-based access control

API-based HackerRank integration
