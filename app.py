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
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

KEY = "DNmoNwfQbaJFsYerLF4A"
isbn = "0765326353"


@app.route("/", methods=["GET", "POST"])
def index():
    session_user = db.execute("SELECT username FROM users WHERE id = :id", {"id": session["user_id"]}).first().username \
        if session.get("user_id") \
        else None

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
            return render_template("index.html", message="You were successfully registered")

        # log in user
        elif rowCount == 1:
            login = db.execute("SELECT username, password FROM users WHERE username = :username", {
                "username": username}).fetchone()

            # password matches
            if password == login.password:
                if username in session:
                    return redirect(url_for("search"))
                else:
                    session["user_id"] = login.username
                    return redirect(url_for("search"))
            # wrong password
            else:
                return render_template("error.html", message="Wrong email/password combination")

    return render_template("index.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
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


@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    user = session["user_id"]  # "test@test.com"
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).first()

    if request.method == "POST":
        rating = int(request.form.get("ratingSelect"))
        comment = str(request.form.get("commentTextArea"))

        check_rating = db.execute("SELECT rating, comment FROM reviews WHERE isbn = :isbn AND username = :user", {
            "isbn": isbn, "user": user}).first()

        if check_rating == None:
            print("INSERTING")
            db.execute("INSERT INTO reviews VALUES (:user, :isbn, :rating, :comment)",
                       {"user": user, "isbn": isbn,
                        "rating": rating, "comment": comment})
            db.commit()
        else:
            print("UPDATING")
            db.execute("UPDATE reviews SET rating = :rating, comment = :comment WHERE isbn = :isbn AND username = :user",
                       {"isbn": isbn, "user": user, "rating": rating, "comment": comment})
            db.commit()

    elif request.method == "GET":
        review = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :user",
                            {"isbn": isbn, "user": user}).first()

        if review != None:
            print("review: " + str(review))
            rating = review.rating
            comment = review.comment
        else:
            rating = 1
            comment = ""

    return render_template("book.html", isbn=book[0], title=book[1], author=book[2], year=book[3],
                           rating=rating, comment=comment)


@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    if request.method == "GET":
        rowCount = int(db.execute("SELECT * FROM books WHERE isbn = :isbn",
                                  {"isbn": isbn}).rowcount)
        if rowCount > 0:
            book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                              {"isbn": isbn}).first()

            review_count = db.execute(
                "SELECT COUNT(*) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).first().count
            average_score = db.execute("SELECT AVG(rating::DECIMAL) FROM reviews WHERE isbn = :isbn",
                                       {"isbn": isbn}).first().avg

            response = {
                "isbn": int(book.isbn),
                "title": book.title,
                "author": book.author,
                "year": int(book.year),
                "review_count": review_count,
                "average_score": float('{0:.2f}'.format(average_score))
            }

            return jsonify(response)

    return render_template("404.html", message="The requested book doesn't exist in our database!")


def goodreads(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": KEY, "isbns": isbn})
    return res.json()['books'][0]


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)  # debug=True
