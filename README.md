<div align="center">

# 🎓 AI Flashcard Creator

**Turn your notes into flashcards and practice exams — instantly, with AI.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20App-667eea?style=for-the-badge&logo=vercel&logoColor=white)](https://ai-flashcard-creator-orcin.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Source%20Code-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/vidhiborse/ai-flashcard-creator)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Gemini API](https://img.shields.io/badge/Google-Gemini%20API-8E75B2?style=flat-square&logo=google&logoColor=white)
![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 📖 Overview

**AI Flashcard Creator** is a full-stack study companion web app that uses Google's **Gemini AI** to turn any PDF, TXT, or Markdown file into ready-to-use **flashcards** and **AI-generated practice exams (MCQs)**. It also includes an **AI Study Buddy chatbot**, a personal **analytics dashboard**, **dark mode**, and a secure **user account system** — all wrapped in a clean, mobile-responsive UI.

🔗 **Live App:** [ai-flashcard-creator-orcin.vercel.app](https://ai-flashcard-creator-orcin.vercel.app/)
📂 **Source Code:** [github.com/vidhiborse/ai-flashcard-creator](https://github.com/vidhiborse/ai-flashcard-creator)

---

## ✨ Features

### 📚 Core Study Tools
- **AI Flashcard Generation** — Upload a PDF/TXT/MD file and generate custom flashcards (choose count & difficulty)
- **AI Practice Exams** — Auto-generated multiple-choice exams from your uploaded material, with a live timer and instant scoring
- **AI Study Buddy Chat** — Ask questions, request explanations, or get quizzed conversationally
- **Export Flashcards** — Download your flashcards as `.txt` or `.json`

### 👤 Account & Personalization
- Secure signup/login with hashed passwords
- Forgot password / email-based password reset
- Editable profile with photo upload
- Persistent **dark mode** (saved per user)
- Account deletion with password confirmation

### 📊 Analytics & Admin
- Personal analytics dashboard (study streaks, scores, activity)
- Admin panel with site-wide stats: total users, flashcards, exams, page views, unique visitors, and most-visited pages
- Google Analytics (GA4) integration
- Database-level visitor/page-view tracking

### 🎨 UX Highlights
- Fully responsive design (mobile, tablet, desktop)
- Smooth animations and micro-interactions across auth & study pages
- Service worker for faster repeat loads
- Accessible, high-contrast UI in both light and dark mode

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask, Flask-Login, Flask-Mail |
| **Database** | PostgreSQL (hosted on [Neon](https://neon.tech)), SQLAlchemy ORM |
| **AI** | Google Gemini API (`google-generativeai`) |
| **Frontend** | HTML5, CSS3 (custom, no framework), Vanilla JavaScript |
| **File Handling** | PyPDF2 (PDF parsing), Pillow (image processing) |
| **Auth & Security** | Flask-Login, Werkzeug password hashing, itsdangerous |
| **Analytics** | Google Analytics 4, custom PostgreSQL page-view tracking |
| **Deployment** | Vercel (serverless), GitHub (CI via auto-deploy on push) |

---

## 🚀 Live Demo

👉 **[https://ai-flashcard-creator-orcin.vercel.app/](https://ai-flashcard-creator-orcin.vercel.app/)**

Try it out — sign up for a free account, upload a PDF of your notes, and generate your first flashcard set in seconds.

---

## 📸 App Walkthrough

1. **Sign Up / Login** — Create an account or log in securely
2. **Upload Notes** — Drop in a PDF, TXT, or MD file on the Study page
3. **Generate Flashcards** — Choose number of cards & difficulty, then let AI do the rest
4. **Take a Practice Exam** — Auto-generated MCQs based on your material, with a timer and scoring
5. **Chat with AI Study Buddy** — Ask follow-up questions or request quizzes
6. **Track Progress** — View stats like study streaks, average scores, and flashcard count on your Analytics page

---

## 🧩 Project Structure

```
AI_Flashcard_Project/
├── web_app.py                 # Main Flask application (routes, logic)
├── models.py                  # SQLAlchemy database models
├── wsgi.py                    # Vercel serverless entry point
├── vercel.json                # Vercel deployment configuration
├── requirements.txt           # Python dependencies
├── .gitignore
├── static/
│   ├── style.css               # Core app styles
│   ├── dark-mode.css           # Dark mode overrides
│   ├── sw.js                   # Service worker
│   ├── logo.jpg / favicon.ico
│   └── profile_photos/         # User-uploaded avatars
└── templates/
    ├── login.html
    ├── signup.html
    ├── forgot_password.html
    ├── reset_password.html
    ├── dashboard.html
    ├── study.html
    ├── chat.html
    ├── profile.html
    ├── analytics.html
    └── admin.html
```

---

## ⚙️ Getting Started Locally

### Prerequisites
- Python 3.10+
- A [Google Gemini API key](https://ai.google.dev/)
- A PostgreSQL database (e.g. a free [Neon](https://neon.tech) instance)
- (Optional) A Gmail App Password for email features

### 1. Clone the repository
```bash
git clone https://github.com/vidhiborse/ai-flashcard-creator.git
cd ai-flashcard-creator
```

### 2. Create a virtual environment & install dependencies
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_flask_secret_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```

### 4. Run the app
```bash
python web_app.py
```

Visit **http://localhost:5000** in your browser.

---

## 🌐 Deployment

This project is deployed on **[Vercel](https://vercel.com)** as a serverless Flask app, connected directly to the GitHub repository for automatic deployments on every push to `main`.

- **Production URL:** [ai-flashcard-creator-orcin.vercel.app](https://ai-flashcard-creator-orcin.vercel.app/)
- **Database:** Neon (serverless PostgreSQL)
- **Deploy trigger:** `git push origin main` → Vercel auto-builds and redeploys

To deploy your own copy:
1. Fork this repository
2. Import it into [Vercel](https://vercel.com/new)
3. Add the environment variables listed above in **Project Settings → Environment Variables**
4. Deploy 🚀

---

## 🗺️ Roadmap

- [ ] Export flashcards to Anki / Quizlet
- [ ] Spaced repetition study mode
- [ ] Public/shareable flashcard sets
- [ ] Pomodoro-style study timer
- [ ] Custom domain

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👩‍💻 Author

**Vidhi Borse**
🔗 GitHub: [@vidhiborse](https://github.com/vidhiborse)

---

<div align="center">

**⭐ If you found this project useful, consider giving it a star on GitHub! ⭐**

[Live Demo](https://ai-flashcard-creator-orcin.vercel.app/) · [Report Bug](https://github.com/vidhiborse/ai-flashcard-creator/issues) · [Request Feature](https://github.com/vidhiborse/ai-flashcard-creator/issues)

</div>