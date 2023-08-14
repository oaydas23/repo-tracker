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
import psycopg2

# Github Token
# /////////////////////////////////////////////////////////////////////////////////////////////////
organization = "maddogtechnology"
token = os.environ['TOKEN']
# /////////////////////////////////////////////////////////////////////////////////////////////////

app = Flask(__name__)

# PostgreSQL Database
# /////////////////////////////////////////////////////////////////////////////////////////////////

table = psycopg2.connect(
    database=os.environ['DATABASE']
    user=os.environ['USER'],
    password=os.environ['PASSWORD'],
    host=os.environ['HOST']
)

cursor = table.cursor()

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

    return render_template("home.html")


# Login, Logout & Register
# /////////////////////////////////////////////////////////////////////////////////////////////////
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id

    session.clear()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS repo_tracker_users (id SERIAL PRIMARY KEY, username TEXT NOT NULL, hash TEXT NOT NULL)"
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
            "SELECT * FROM repo_tracker_users WHERE username = (%s)", (request.form.get("username"),)
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
        table.commit()
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        table.commit()
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
            "SELECT * FROM repo_tracker_users WHERE username = (%s)", (request.form.get("username"),)
        )
        rows = cursor.fetchall()

        if len(rows) == 1:
            return render_template("register.html")
        
        # Insert username and password
        cursor.execute(
            "INSERT INTO repo_tracker_users (username, hash) VALUES(%s, %s)",
            (request.form.get("username"), generate_password_hash(password)),
        )

        cursor.execute(
            "SELECT * FROM repo_tracker_users WHERE username = (%s)", (request.form.get("username"),)
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

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS repo_tracker_gradle ("
        "id SERIAL PRIMARY KEY, "
        "pname TEXT, "
        "gname TEXT, "
        "bnum TEXT, "
        "bdate TEXT, "
        "artifacts TEXT)"
    )

    if request.method == "GET":
        cursor.execute("SELECT pname, gname, bnum, bdate, artifacts FROM repo_tracker_gradle")
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
            "INSERT OR IGNORE INTO repo_tracker_gradle (pname, gname, bnum, bdate, artifacts) "
            "VALUES(%s, %s, %s, %s, %s)",
            (pname, gname, bnum, bdate, artifacts),
        )

        cursor.execute("SELECT pname, gname, bnum, bdate, artifacts FROM repo_tracker_gradle")
        gradle_input = cursor.fetchall()

        table.commit()
        return render_template("artifacts.html", input=gradle_input)


@app.route("/commit", methods=["POST", "GET"])
def commit():

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS repo_tracker_commits ("
        "id SERIAL PRIMARY KEY, "
        "repo TEXT, "
        "message TEXT, "
        "author TEXT, "
        "date TEXT, "
        "archive TEXT)"
    )

    if request.method == "GET":
        cursor.execute(
            "SELECT repo, message, author, date, archive FROM repo_tracker_commits ORDER BY date ASC"
        )
        data = cursor.fetchall()

        return render_template("commits.html", data=data)

    if request.method == "POST":
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/orgs/{organization}/repos"

        repo_names = []

        # Fetch all pages of repositories
        while url:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                repos = response.json()
                repo_names.extend([repo["name"] for repo in repos])
                
                # Check for pagination
                url = response.links.get("next", {}).get("url")
            else:
                print("Error:", response.status_code)
                break

        i=0
        for repo in repo_names:
            i +=1
            print (f"Progress: {i}")

            url = f"https://api.github.com/repos/MadDogTechnology/{repo}"
            response = requests.get(url, headers=headers)

            try:
                rep = response.json()['name']
                archive = response.json()['archived']
            except:
                continue

            url = f"https://api.github.com/repos/MadDogTechnology/{repo}/commits"
            response = requests.get(url, headers=headers)

            try:
                count = 0
                message = response.json()[count]['commit']['message']
                while "README" in message.upper():
                    count += 1
                    message = response.json()[count]['commit']['message']

                c = response.json()[count]['commit']['message']
                author = response.json()[count]['commit']['author']['name']
                date = response.json()[count]['commit']['author']['date']

                cursor.execute(
                    "INSERT INTO repo_tracker_commits (repo, message, author, date, archive) "
                    "VALUES(%s, %s, %s, %s, %s)",
                    (rep, c, author, date, archive),
                )
            except:
                c = "N/A"
                author = "N/A"
                date = "N/A"

                cursor.execute(
                    "INSERT INTO repo_tracker_commits (repo, message, author, date, archive) "
                    "VALUES(%s, %s, %s, %s, %s)",
                    (rep, c, author, date, archive),
                )
                continue

        cursor.execute(
            "SELECT repo, message, author, date, archive FROM repo_tracker_commits ORDER BY date ASC"
        )
        data = cursor.fetchall()

        table.commit()
        return render_template("commits.html", data=data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1000))
    app.run(debug=True, host="0.0.0.0", port=port)









