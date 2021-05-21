
import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/home_page")
def home_page():
    return render_template("homepage.html")


@app.route("/")
@app.route("/get_books")
def get_books():
    allbooks = list(mongo.db.allbooks.find())
    return render_template("books.html", allbooks=allbooks)


@app.route("/search", methods=["GET", "POST"])
def search():
    """search:

    * Connects to database for words (String) entered in search bar.
    \n Args:
    * None.
    \n Returns:
    * Template with the search field access allbooks\
    containing search words.
    """

    query = request.form.get("query")
    allbooks = list(mongo.db.allbooks.find({"$text": {"$search": query}}))
    return render_template("books.html", allbooks=allbooks)


@app.route("/register", methods=["GET", "POST"])
def register():
    """register:
    * Checks if username exists in db.
    * Will return user to registration page with a flash\
    error message if user not new.
    \n Args:
    * None.
    \n Returns:
    * user profile will appear if successful.
    * register page with flash displaying error if unsuccessful.
    """

    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """login:
    * Checks if username exists in db.
    * Logs user name and password to check for  match.
    * Appends username to session['user'] cookie.
    Args:
    * None.
    
     Returns:
    * User profile will appear if successful.
    * Login page with flash displaying error if unsuccessful.
    """

    if request.method == 'POST':
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """profile:
    * Searches for a users' book reviews
    \n Args:
    * username
    \n Returns:
    * User book reviews for their profile page.
    """

    # grab the session user's username from db
    if "user" in session:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        if session["user"] == username:
            allbooks = list(mongo.db.allbooks.find({"created_by": username}))
            return render_template("profile.html",
                                   allbooks=allbooks, username=username)

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """logout:
    * Removes user from session.
    \n Args:
    * None
    \n Returns:
    *   Confirmation user is logged out.
    """

    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    """add_review:
    * Posts user review from form to MongoDB
     Returns:
    * Submits user review form to MongoDB
    """

    if "user" in session:
        if request.method == "POST":
            allbooks = {
                "genre_name": request.form.get("genre_name"),
                "book_title": request.form.get("book_title"),
                "author": request.form.get("author"),
                "review": request.form.get("review"),
                "rating": request.form.get("rating"),
                "image_url": request.form.get("image_url"),
                "buy_link": request.form.get("buy_link"),
                "created_by": session["user"]
            }
            mongo.db.books.insert_one(allbooks)
            flash("Review Successfully Added")
            return redirect(url_for("get_books"))

        genres = mongo.db.genres.find().sort("genre_name", 1)
        return render_template("add_review.html", genres=genres)

    return redirect(url_for("login"))


@app.route("/edit_book/<allbooks_id>", methods=["GET", "POST"])
def edit_book(allbooks_id):
    """edit_book:
    * Allows user to submit changes to own review.
    * Allows admin to allow update reviews and post\
        affiliate links.
        Args:
    * book_id
     Returns:
    * Updated review if changes were made successfully.
    """

    if "user" in session:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        allbooks = mongo.db.allbooks.find_one({"_id": ObjectId(allbooks_id)})
        if allbooks["created_by"] == username or session["user"] == "admin":
            if request.method == "POST":
                submit = {
                    "genre_name": request.form.get("genre_name"),
                    "book_title": request.form.get("book_title"),
                    "author": request.form.get("author"),
                    "book_review": request.form.get("book_review"),
                    "book_rating": request.form.get("book_rating"),
                    "image_url": request.form.get("image_url"),
                    "buy_link": request.form.get("buy_link"),
                    "created_by": session["user"]
                }
                mongo.db.books.update({"_id": ObjectId(allbooks_id)}, submit)
                flash("Review Successfully Updated")

            category = mongo.db.genres.find().sort("category_name", 1)
            return render_template(
                "edit_review.html", allbooks=allbooks,
                genres=genres)

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.route("/delete_book/<allbooks_id>")
def delete_book(allboosk_id):
    """delete_book:
    * Allows user to delete own review.
    * Allows admin to delete book reviews.
    \n Args:
    * book_id
    \n Returns:
    * Delete review and confirm successful.
    """

    if "user" in session:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        allbooks = mongo.db.allbooks.find_one({"_id": ObjectId(allbooks_id)})
        if allbooks["created_by"] == username or session["user"] == "admin":

            mongo.db.books.remove({"_id": ObjectId(allbooks_id)})
            flash("Book Review Successfully Deleted")
            return redirect(url_for("get_books"))

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.route("/get_genres")
def get_genres():
    """get_genres:
    * Allows admin to access the manage genres\
        page.
    \n Args:
    * None.
    \n Returns:
    * Renders manage genres webpage.
    """

    if "user" in session:
        if session["user"] == "admin":

            category = list(mongo.db.genres.find().sort("category_name", 1))
            return render_template("category.html", category=category)

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    """add_genre:
    * Allows admin to add new genres.
    \n Args:
    * None.
    \n Returns:
    * Posts new genre to MongoDB and confirms successful.
    """

    if "user" in session:
        if session["user"] == "admin":
            if request.method == "POST":
                genre = {
                    "genre_name": request.form.get("genre_name")
                }
                mongo.db.genres.insert_one(genre)
                flash("New Category Added")
                return redirect(url_for("get_Category"))

            return render_template("add_Catergory.html")

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.route("/edit_genre/<category_id>", methods=["GET", "POST"])
def edit_catergory(category_id):
    """edit_genre:
    * Allows admin to update genres.
    \n Args:
    * genre_id
    \n Returns:
    * Updated genre and confirmation message if successful.
    """

    if "user" in session:
        if session["user"] == "admin":

            if request.method == "POST":
                submit = {
                    "category_name": request.form.get("category_name")
                }
                mongo.db.genres.update({"_id": ObjectId(genre_id)}, submit)
                flash("Genre Successfully Updated")
                return redirect(url_for("get_genres"))

            genre = mongo.db.genres.find_one({"_id": ObjectId(category_id)})
            return render_template("edit_catergory.html", category=category)

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.route("/delete_genre/<genre_id>")
def delete_genre(genre_id):
    """delete_genre:
    * Allows admin to remove genre.
    \n Args:
    * genre_id
    \n Returns:
    * Deletes genre and confirms if it was succesful.
    """

    if "user" in session:
        if session["user"] == "admin":

            mongo.db.category.remove({"_id": ObjectId(category_id)})
            flash("Genre Successfully Deleted")
            return redirect(url_for("get_category"))

        return redirect(url_for("get_books"))

    return redirect(url_for("login"))


@app.errorhandler(404)
def page_not_found(e):
    """page_not_found:
    * Responds to 404 error when page not found.
    \n Args:
    * e
    \n Returns:
    * Error message.
    """

    return render_template("error.html"), 404


@app.errorhandler(500)
def internal_error(e):
    """internal_error:
    * Responds to 500 internal error.
    \n Args:
    * e
    \n Returns:
    * Error message.
    """

    return render_template("error.html"), 500


@app.errorhandler(503)
def service_unavailable(e):
    """service_unavailable:
    * Responds to 503 when service unavailable.
    \n Args:
    * e
    \n Returns:
    * Error message.
    """

    return render_template("error.html"), 503


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT","5000")),
            debug=True)