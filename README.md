# AI Flashcard Creator

A full-stack web application that uses Google's Gemini AI to convert study material (PDF, TXT, or Markdown) into flashcards and practice exams. Includes an AI chat assistant, user accounts, analytics, and an admin dashboard.

Live app: https://ai-flashcard-creator-orcin.vercel.app/
Repository: https://github.com/vidhiborse/ai-flashcard-creator

## Overview

I built this project to make studying from raw notes faster. Instead of manually writing flashcards, you upload your notes and the app generates question-answer pairs and multiple-choice practice exams using the Gemini API. It also includes a study chatbot, progress tracking, and a full authentication system with profile management.

## Features

**Study tools**
- Generate flashcards from PDF/TXT/MD files, with adjustable count and difficulty
- Generate multiple-choice practice exams with a timer and automatic scoring
- AI chat assistant for asking questions or requesting explanations
- Export flashcards as TXT or JSON

**Accounts**
- Signup and login with hashed passwords
- Forgot password flow with email reset link
- Editable profile, including profile photo upload
- Account deletion with password confirmation
- Dark mode preference saved per user

**Analytics and admin**
- Personal dashboard showing study streaks, scores, and activity
- Admin panel with site-wide stats: total users, flashcards, exams, page views, and most-visited pages
- Google Analytics integration
- Page view tracking stored in the database

## Tech stack

- Backend: Python, Flask, Flask-Login, Flask-Mail
- Database: PostgreSQL (Neon), SQLAlchemy
- AI: Google Gemini API
- Frontend: HTML, CSS, vanilla JavaScript (no framework)
- File handling: PyPDF2, Pillow
- Deployment: Vercel, with GitHub for version control and auto-deploy

## Project structure

```
AI_Flashcard_Project/
├── web_app.py              Main Flask app and routes
├── models.py                Database models
├── wsgi.py                  Vercel entry point
├── vercel.json               Vercel config
├── requirements.txt
├── static/
│   ├── style.css
│   ├── dark-mode.css
│   ├── sw.js
│   └── profile_photos/
└── templates/
    ├── login.html
    ├── signup.html
    ├── forgot_password.html
    ├── dashboard.html
    ├── study.html
    ├── chat.html
    ├── profile.html
    ├── analytics.html
    └── admin.html
```

## Running locally

Requirements: Python 3.10+, a Gemini API key, and a PostgreSQL database (a free Neon instance works fine).

Clone the repo and install dependencies:

```bash
git clone https://github.com/vidhiborse/ai-flashcard-creator.git
cd ai-flashcard-creator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```

Run the app:

```bash
python web_app.py
```

The app will be available at http://localhost:5000

## Deployment

The app is deployed on Vercel and connected to this GitHub repository. Pushing to the main branch triggers an automatic redeploy. The database is hosted on Neon (serverless PostgreSQL).

## Possible improvements

- Export flashcards to Anki or Quizlet format
- Spaced repetition mode
- Shareable public flashcard sets
- Custom domain

## Author

Vidhi Borse
GitHub: https://github.com/vidhiborse