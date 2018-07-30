import os
import requests

from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))  # DATABASE_URL
db = scoped_session(sessionmaker(bind=engine))

KEY = "DNmoNwfQbaJFsYerLF4A"
isbn = "0765326353"


@app.route("/", methods=["GET", "POST"])
def index():
    # Get form information
    if request.method == "POST":
        username = str(request.form.get("inputEmail"))
        password = str(request.form.get("inputPassword"))

        rowCount = int(db.execute(
            "SELECT * FROM users WHERE username = :username", {"username": username}).rowcount)

        print(rowCount)

        # register new user
        if rowCount == 0:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {
                "username": username, "password": password})
            db.commit()
            return render_template("success.html", message="You were successfully registered")
        # log in existing user
        elif rowCount == 1:
            checkPassword = db.execute("SELECT password FROM users WHERE username = :username", {
                "username": username}).fetchone()
            # log in successful
            if password == checkPassword.password:
                if username in session:
                    return render_template("index.html")
                else:
                    return render_template("success.html", message="Successfully logged in. Welcome!")
            # wrong password
            else:
                return render_template("error.html", message="Wrong password")

    return render_template("index.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/search")
def search():
    if username in session:
        return render_template("search.html")
    else:
        return render_template("error.html", message="Sorry! You need to log in first to use that feature")

# GoodReads API
# res = requests.get("https://www.goodreads.com/book/review_counts.json",
#                    params={"key": KEY, "isbn": isbn})
# print(res.json())
