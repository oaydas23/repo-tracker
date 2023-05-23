from github import Github
import csv
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

g = Github("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")
org = g.get_organization("MadDogTechnology")

app = Flask(__name__)


# check to see if data is added properly
# cursor.execute("SELECT * FROM dataREAL WHERE id < ?", (50,))
# wow = cursor.fetchall()
# print(wow)


@app.route("/", methods=["POST", "GET"])
def index():
    table = sqlite3.connect('database.db')
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

        return render_template("home.html", data=data)

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

                        if not check:
                            cursor.execute("INSERT OR IGNORE INTO dataREAL (repo, message, author, date, archive) "
                                           "VALUES(?, ?, ?, ?, ?)",
                                           (rep, c, author, date, archive))

                        # excel file code
                        # data["repo"].append(repo.name)
                        # data["commit"].append(latest_commit.commit.message)
                        # data["author"].append(latest_commit.commit.author.name)
                        # data["date"].append(latest_commit.commit.author.date)
                        # data["archived"].append(repo.archived)

                        change = True
                else:
                    change = True
            count += 1
            print("PROGRESS: ", round((count/349)*100, 2), "%")

        cursor.execute("SELECT repo, message, author, date, archive FROM dataREAL")
        data = cursor.fetchall()

        table.commit()
        return render_template("home.html", data=data)
    table.close()

# excel file code
# transpose = list(zip(*data.values()))

# filename = 'output.csv'

# with open(filename, 'w', newline='') as csvfile:
    # writer = csv.writer(csvfile)
    # cat = ["Repo", "Commit", "Author", "Date", "Archive"]
    # writer.writerow(cat)
    # writer.writerows(transpose)