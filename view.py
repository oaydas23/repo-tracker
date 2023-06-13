from github import Github
import os
import sqlite3
from datetime import datetime
import random
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import string
import requests
import urllib.parse
from random import sample
import re
from functools import wraps

# Github Token
# /////////////////////////////////////////////////////////////////////////////////////////////////
g = Github("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")
org = g.get_organization("MadDogTechnology")
# /////////////////////////////////////////////////////////////////////////////////////////////////

app = Flask(__name__)

# PostgreSQL Database
# /////////////////////////////////////////////////////////////////////////////////////////////////
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://postgres:password@localhost:5000/repo"
db = SQLAlchemy(app)


# Commit Table
class Commit(db.Model):
    __tablename__ = "commits"
    id = db.Column(db.Integer, primary_key=True)
    repo = db.Column(db.String)
    message = db.Column(db.String)
    author = db.Column(db.String)
    date = db.Column(db.String)
    archive = db.Column(db.String)

    def __init__(self, repo, message, author, date, archive):
        self.repo = repo
        self.message = message
        self.author = author
        self.date = date
        self.archive = archive


# Gradle Table
class Gradle(db.Model):
    __tablename__ = "gradle"
    id = db.Column(db.Integer, primary_key=True)
    pname = db.Column(db.String)
    gname = db.Column(db.String)
    bnum = db.Column(db.String)
    bdate = db.Column(db.String)
    artifacts = db.Column(db.String)

    def __init__(self, pname, gname, bnum, bdate, artifacts):
        self.pname = pname
        self.gname = gname
        self.bnum = bnum
        self.bdate = bdate
        self.artifacts = artifacts


# Users Table
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    hash = db.Column(db.String)

    def __init__(self, username, hash):
        self.username = username
        self.hash = hash


# /////////////////////////////////////////////////////////////////////////////////////////////////

# Session
# /////////////////////////////////////////////////////////////////////////////////////////////////
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# /////////////////////////////////////////////////////////////////////////////////////////////////


# Login
# /////////////////////////////////////////////////////////////////////////////////////////////////
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# /////////////////////////////////////////////////////////////////////////////////////////////////


@app.route("/", methods=["GET"])
@login_required
def index():
    db.create_all()

    return render_template("home.html")


# Login, Logout & Register
# /////////////////////////////////////////////////////////////////////////////////////////////////
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id

    session.clear()
    table = sqlite3.connect("data/database.db")
    cursor = table.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(id))"
    )

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html")

        # Query database for username
        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()
    table = sqlite3.connect("data/database.db")
    cursor = table.cursor()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html")
        
        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html")
        password = request.form.get("password")

        # Ensure password meets the requirements
        if (
            len(password) < 8
            or not re.search(r"[A-Z]", password)
            or not re.search(r"[!@#$%^&*()_+\-=[\]{};':\"\\|,.<>/?]", password)
        ):
            return render_template("register.html")
        
        # Ensure confirmation matches the password
        elif request.form.get("confirmation") != password:
            return render_template("register.html")
        
        # Query database for existing username
        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )
        rows = cursor.fetchall()

        if len(rows) == 1:
            return render_template("register.html")
        
        # Insert username and password

        # user=User(request.form.get("username"), generate_password_hash(request.form.get("password")))
        # db.session.add(user)
        # db.session.commit()

        cursor.execute(
            "INSERT INTO users (username, hash) VALUES(?, ?)",
            (request.form.get("username"), generate_password_hash(password)),
        )

        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )
        rows = cursor.fetchall()

        session["user_id"] = rows[0][0]
        table.commit()

        return redirect("/")
    
    else:
        return render_template("register.html")


# /////////////////////////////////////////////////////////////////////////////////////////////////


@app.route("/artifact", methods=["GET", "POST"])
def artifact():
    table = sqlite3.connect("data/database.db")
    cursor = table.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS gradle ("
        "id INTEGER PRIMARY KEY, "
        "pname TEXT, "
        "gname TEXT, "
        "bnum TEXT, "
        "bdate TEXT, "
        "artifacts TEXT)"
    )

    if request.method == "GET":
        cursor.execute("SELECT pname, gname, bnum, bdate, artifacts FROM gradle")
        gradle_input = cursor.fetchall()
        return render_template("artifacts.html", input=gradle_input)

    if request.method == "POST":
        now = datetime.now()
        current_time = now.strftime("%D" + "  " + "%H:%M:%S")

        data = request.get_json()
        pname = data["pname"]
        gname = data["gname"]
        bnum = data["bnum"]
        bdate = current_time
        artifacts = ""

        for art in data["artifacts"]:
            artifacts = artifacts + art + "\n"

        cursor.execute(
            "INSERT OR IGNORE INTO gradle (pname, gname, bnum, bdate, artifacts) "
            "VALUES(?, ?, ?, ?, ?)",
            (pname, gname, bnum, bdate, artifacts),
        )

        cursor.execute("SELECT pname, gname, bnum, bdate, artifacts FROM gradle")
        gradle_input = cursor.fetchall()

        table.commit()
        return render_template("artifacts.html", input=gradle_input)

    table.close()


@app.route("/commit", methods=["POST", "GET"])
def commit():
    table = sqlite3.connect("data/database.db")
    cursor = table.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS dataREAL ("
        "id INTEGER PRIMARY KEY, "
        "repo TEXT, "
        "message TEXT, "
        "author TEXT, "
        "date TEXT, "
        "archive TEXT)"
    )

    if request.method == "GET":
        cursor.execute(
            "SELECT repo, message, author, date, archive FROM dataREAL ORDER BY date ASC"
        )
        data = cursor.fetchall()

        return render_template("commits.html", data=data)

    if request.method == "POST":
        change = False
        i = 0
        count = 0

        repos = list(org.get_repos())
        total = len(repos)

        for repo in repos:
            change = False
            i = 0
            while not change:
                # checks for empty repo
                try:
                    commits = list(repo.get_commits())
                except Exception as e:
                    if "This repository is empty" in str(e):
                        print("EMPTY REP")
                        change = True

                # checks if all commits are README
                length = len(commits)

                if i < length:
                    latest_commit = commits[i]
                    if "README" in latest_commit.commit.message.upper():
                        change = False
                        i += 1
                    else:
                        rep = str(repo.name)
                        c = str(latest_commit.commit.message)
                        author = str(latest_commit.commit.author.name)
                        date = str(latest_commit.commit.author.date)
                        archive = str(repo.archived)

                        # database code
                        cursor.execute("SELECT id FROM dataREAL WHERE repo = ?", (rep,))
                        check = cursor.fetchall()
                        if check:
                            cursor.execute(
                                "DELETE FROM dataREAL WHERE repo = ?", (rep,)
                            )
                            cursor.execute(
                                "INSERT OR IGNORE INTO dataREAL (repo, message, author, date, archive) "
                                "VALUES(?, ?, ?, ?, ?)",
                                (rep, c, author, date, archive),
                            )
                        else:
                            cursor.execute(
                                "INSERT OR IGNORE INTO dataREAL (repo, message, author, date, archive) "
                                "VALUES(?, ?, ?, ?, ?)",
                                (rep, c, author, date, archive),
                            )

                        change = True
                else:
                    change = True
            count += 1
            print("PROGRESS: ", round((count / total) * 100, 2), "%")

        cursor.execute(
            "SELECT repo, message, author, date, archive FROM dataREAL ORDER BY date ASC"
        )
        data = cursor.fetchall()

        table.commit()
        return render_template("commits.html", data=data)
    table.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1000))
    app.run(debug=True, host="0.0.0.0", port=port)
