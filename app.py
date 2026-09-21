import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, time
from zoneinfo import ZoneInfo

from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

# ============================================================
# DATABASE SETUP
# ============================================================
DB_PATH = "inquiries.db"


def init_db():
    """Create the inquiries table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_inquiry(name, email, message):
    """Save a new inquiry to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inquiries (name, email, message) VALUES (?, ?, ?)",
        (name, email, message),
    )
    conn.commit()
    conn.close()


def get_all_inquiries():
    """Fetch all inquiries, newest first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inquiries ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


# Create the table on startup
init_db()


# ============================================================
# STORE HOURS + STATUS
# ============================================================
STORE_HOURS = {
    "Monday": "8am – 6pm",
    "Tuesday": "8am – 6pm",
    "Wednesday": "8am – 6pm",
    "Thursday": "8am – 6pm",
    "Friday": "8am – 6pm",
    "Saturday": "8am – 5pm",
    "Sunday": "9am – 2pm",
}


def format_time(t):
    hour = t.hour
    minute = t.minute
    period = "am" if hour < 12 else "pm"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    if minute == 0:
        return f"{display_hour}{period}"
    return f"{display_hour}:{minute:02d}{period}"


def get_store_status(now):
    day = now.weekday()
    current_time = now.time()

    if day == 6:
        open_time, close_time = time(9, 0), time(14, 0)
    elif day == 5:
        open_time, close_time = time(8, 0), time(17, 0)
    else:
        open_time, close_time = time(8, 0), time(18, 0)

    is_open = open_time <= current_time < close_time
    if is_open:
        message = f"Open now · Closes {format_time(close_time)}"
    else:
        message = f"Closed · Opens {format_time(open_time)}"
    return {"is_open": is_open, "message": message}


@app.context_processor
def inject_store_status():
    now = datetime.now(ZoneInfo("Africa/Johannesburg"))
    return {
        "store_status": get_store_status(now),
        "store_hours": STORE_HOURS,
        "today_name": now.strftime("%A"),
    }


# ============================================================
# EMAIL (optional — will work once .env is set up)
# ============================================================
def send_email(customer_name, customer_email, message):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("⚠️ Email not configured. Skipping send.")
        return False

    msg = MIMEMultipart()
    msg["From"] = MAIL_USERNAME
    msg["To"] = MAIL_USERNAME
    msg["Subject"] = f"New Website Inquiry from {customer_name}"
    msg["Reply-To"] = customer_email

    body = f"""
    You have a new inquiry from your website!

    Name: {customer_name}
    Email: {customer_email}

    Message:
    {message}

    ---
    Reply directly to this email to respond to {customer_name}.
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False


# ============================================================
# ROUTES
# ============================================================
@app.route("/", methods=["GET", "POST"])
def home():
    greeting = ""
    if request.method == "POST":
        name = request.form.get("username")
        email = request.form.get("email")
        message = request.form.get("message")

        # Save to database — this ALWAYS works
        save_inquiry(name, email, message)

        # Try to send email (optional — works once .env is set up)
        send_email(name, email, message)

        greeting = name

    return render_template("index.html", greeting=greeting)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/specials")
def specials():
    return render_template("specials.html")


# ============================================================
# LOCAL ADMIN PAGE (view inquiries)
# Access: http://127.0.0.1:5000/inquiries?key=YOUR_KEY
# Set ADMIN_KEY in .env, or it defaults to "changeme"
# ============================================================
@app.route("/inquiries")
def inquiries():
    key = request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return "🔒 Not authorized. Add ?key=YOUR_KEY to the URL.", 403

    all_inquiries = get_all_inquiries()
    return render_template("inquiries.html", inquiries=all_inquiries)


if __name__ == "__main__":
    app.run(debug=True)