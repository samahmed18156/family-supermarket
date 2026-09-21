from flask import Flask, render_template, request

app = Flask(__name__)


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