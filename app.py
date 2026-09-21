from flask import Flask, render_template, request
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)


def format_time(t):
    """Convert 18:00 to 6pm for display."""
    hour = t.hour
    minute = t.minute
    period = "am" if hour < 12 else "pm"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    if minute == 0:
        return f"{display_hour}{period}"
    return f"{display_hour}:{minute:02d}{period}"


def get_store_status():
    """Check if the store is currently open based on Cape Town time."""
    now = datetime.now(ZoneInfo("Africa/Johannesburg"))
    day = now.weekday()  # 0 = Monday, 6 = Sunday
    current_time = now.time()

    # 👇 Change these hours if needed 👇
    if day == 6:  # Sunday
        open_time, close_time = time(8, 0), time(14, 0)
    elif day == 5:  # Saturday
        open_time, close_time = time(8, 0), time(18, 0)
    else:  # Monday - Friday
        open_time, close_time = time(8, 0), time(18, 0)

    is_open = open_time <= current_time < close_time

    if is_open:
        message = f"Open now · Closes {format_time(close_time)}"
    else:
        message = f"Closed · Opens {format_time(open_time)}"

    return {"is_open": is_open, "message": message}


@app.context_processor
def inject_store_status():
    """Makes store_status available in every template automatically."""
    return {"store_status": get_store_status()}


@app.route("/", methods=["GET", "POST"])
def home():
    greeting = ""
    if request.method == "POST":
        username = request.form.get("username")
        greeting = f"{username}"
    return render_template("index.html", greeting=greeting)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/specials")
def specials():
    return render_template("specials.html")


if __name__ == "__main__":
    app.run(debug=True)