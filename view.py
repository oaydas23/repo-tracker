from github import Github
import csv
import os
import sqlite3
from flask import Flask, render_template, request
from datetime import datetime


g = Github("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")
org = g.get_organization("MadDogTechnology")

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("home.html")


@app.route("/artifact", methods=["GET", "POST"])
def artifact():
    table = sqlite3.connect('data/database.db')
    cursor = table.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS gradle ("
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

        cursor.execute("INSERT OR IGNORE INTO gradle (pname, gname, bnum, bdate, artifacts) "
                       "VALUES(?, ?, ?, ?, ?)",
                       (pname, gname, bnum, bdate, artifacts))

        cursor.execute("SELECT pname, gname, bnum, bdate, artifacts FROM gradle")
        gradle_input = cursor.fetchall()

        table.commit()
        return render_template("artifacts.html", input=gradle_input)

    table.close()


@app.route("/commit", methods=["POST", "GET"])
def commit():
    table = sqlite3.connect('data/database.db')
    cursor = table.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS dataREAL ("
                   "id INTEGER PRIMARY KEY, "
                   "repo TEXT, "
                   "message TEXT, "
                   "author TEXT, "
                   "date TEXT, "
                   "archive TEXT)"
                   )

    if request.method == "GET":
        cursor.execute("SELECT repo, message, author, date, archive FROM dataREAL ORDER BY date ASC")
        data = cursor.fetchall()

        return render_template("commits.html", data=data)

    if request.method == "POST":
        change = False
        i = 0
        count = 0

        repos = list(org.get_repos())

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
                            cursor.execute("DELETE FROM dataREAL WHERE repo = ?", (rep,))
                            cursor.execute("INSERT OR IGNORE INTO dataREAL (repo, message, author, date, archive) "
                                           "VALUES(?, ?, ?, ?, ?)",
                                           (rep, c, author, date, archive))
                        else:
                            cursor.execute("INSERT OR IGNORE INTO dataREAL (repo, message, author, date, archive) "
                                           "VALUES(?, ?, ?, ?, ?)",
                                           (rep, c, author, date, archive))

                        change = True
                else:
                    change = True
            count += 1
            print("PROGRESS: ", round((count/349)*100, 2), "%")

        cursor.execute("SELECT repo, message, author, date, archive FROM dataREAL ORDER BY date ASC")
        data = cursor.fetchall()

        table.commit()
        return render_template("commits.html", data=data)
    table.close()


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
