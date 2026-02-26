from web_app import app

# This is for Vercel serverless functions
app = app

if __name__ == "__main__":
    app.run()