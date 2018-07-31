import os
import requests

from flask import Flask, session, render_template, request, flash, redirect, url_for, jsonify
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
            return render_template("search.html", message="You were successfully registered")
        # log in existing user
        elif rowCount == 1:
            checkPassword = db.execute("SELECT password FROM users WHERE username = :username", {
                "username": username}).fetchone()
            # log in successful
            if password == checkPassword.password:
                if username in session:
                    return redirect(url_for("search"))
                    # return render_template("search.html")
                else:
                    return redirect(url_for("search"))
                    # return render_template("search.html", message="Welcome back!")
            # wrong password
            else:
                return render_template("error.html", message="Wrong email/password combination")

    return render_template("index.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        book = str(request.form.get("inputBook"))
        print("book: " + book)

        rowCount = int(db.execute(
            "SELECT * FROM books WHERE isbn LIKE :book OR lower(title) LIKE :book OR lower(author) LIKE :book", {"book": "%" + book + "%"}).rowcount)

        print("rowCount: " + str(rowCount))

        if rowCount == 0:
            return render_template("error.html", message="No matches found")
        else:
            books = db.execute(
                "SELECT * FROM books WHERE isbn LIKE :book OR lower(title) LIKE :book OR lower(author) LIKE :book", {"book": "%" + book + "%"}).fetchall()

            number_results = "Found %d results" % rowCount
            return render_template("results.html", message=number_results, books=books)

        return render_template("search.html")

    else:
        return render_template("search.html")
    # return redirect(url_for("search"))


@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).first()

    # When users click on a book from the results of the search page, they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on your website.

    return render_template("book.html", isbn=book[0], title=book[1], author=book[2], year=book[3], goodreadsdata=goodreads(isbn))


# @app.route("/api/<string:isbn>")
# def api(isbn):
#     return jsonify(book_data(isbn))


@app.route("/api/<string:isbn>")
def api(isbn):
    rowCount = int(db.execute("SELECT * FROM books WHERE isbn = :isbn",
                              {"isbn": isbn}).rowcount)
    if rowCount > 0:
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                          {"isbn": isbn}).first()

        review_count = db.execute(
            "SELECT COUNT(*) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).first().count
        average_score = db.execute(
            "SELECT AVG(rating::DECIMAL) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).first().avg

        response = {
            "isbn": int(book.isbn),
            "title": book.title,
            "author": book.author,
            "year": int(book.year),
            "review_count": review_count,
            "average_score": average_score
        }

        return jsonify(response)

    return render_template("404.html", message="The requested book doesn't exist in our database!")


def goodreads(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": KEY, "isbns": isbn})
    print(res.json())
    return res.json()['books'][0]


if __name__ == '__main__':
    app.run(debug=True)
