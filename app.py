import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import os

from helpers import available_moods, bases, keys, strings

CHUNK = 1024

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///zoroaster.db")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        print("Got executed")
        user_sql = db.execute("SELECT name FROM users WHERE id = ?", session.get("user_id"))
        name = user_sql[0]["name"]
        print(name)
        return render_template("index_logged.html", name = name)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Receive all necessary elements from HTML
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        name = request.form.get("firstname")

        # Check for blank forms
        if username == "":
            return render_template("register.html", error = "Invalid username input.")
        if password == "" or confirmation == "":
            return render_template("register.html", error = "Invalid password.")

        # Check if password and password confirmation are the same
        if password != confirmation:
            return render_template("register.html", error = "Passwords don't match.")

        #Check if username is taken
        all_usernames = db.execute("SELECT username FROM users")
        if all_usernames:
            for index in all_usernames:
                if "username" in index:
                    checked_username = index["username"]
                    if checked_username == username:
                        return render_template("register.html", error = "Username taken.")

         #Hash password
        hashed_password = generate_password_hash(password)
         #Insert into database
        db.execute(
            "INSERT INTO users (username, password, name) VALUES(?, ?, ?)", username, hashed_password, name
        )
        return render_template("index.html", error="You are succesfully registered")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error="Must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error="Username invalid")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return render_template("login.html", error="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        #Get the user's name
        user_sql = db.execute("SELECT name FROM users WHERE id = ?", session.get("user_id"))
        name = user_sql[0]["name"]
        print(name)

        # Redirect user to home page
        return render_template("index_logged.html", error="You are succesfully logged in.", name = name)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return render_template("index.html", error="You are succesfully logged out")

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@app.route("/history")
@login_required
def history():
    track_headers = db.execute("SELECT name, time FROM tracks WHERE user = ?", session.get("user_id"))
    return render_template("history.html", headers = track_headers)

@app.route("/track1", methods=["GET", "POST"])
@login_required
def track1():
    if request.method == "GET":
        #Splits the moods into two lists for improved display. Manipulate modulo to create more lists
        moods_firsthalf = []
        moods_secondhalf = []
        for i in range(len(available_moods)):
            if i % 2 == 0:
                moods_firsthalf.append(available_moods[i])
            else:
                moods_secondhalf.append(available_moods[i])

            print(moods_firsthalf)
            print(moods_secondhalf)
        return render_template("moodselection.html", moods_firsthalf=moods_firsthalf, moods_secondhalf=moods_secondhalf)
    else:
        moodtrial_sql = db.execute("SELECT mood FROM moods WHERE user_ID = ?", session.get("user_id"))
        moodtrial = moodtrial_sql[0]["mood"]
        if moodtrial == "":
            return render_template("moodselection.html", available_moods=available_moods, error="Please select at least one mood")
        return render_template("createtrack.html", bases=bases, keys=keys, strings=strings)

@app.route('/process_moods', methods = ['POST'])
def process():
    print("Hell yeah we got the moods")
    db.execute("DELETE FROM moods WHERE user_ID = ?", session.get("user_id"))
    moods_list = request.get_json()
    moods = ""
    for i in range(len(moods_list)):
        moods += moods_list[i]
        moods = "-".join(moods_list)
    moods_proper = moods.translate({ord("'"): None})
    print(moods_proper)
    db.execute("INSERT INTO moods(mood, user_ID) VALUES (?, ?)", moods_proper, session.get("user_id"))
    return moods

@app.route('/static/sounds/<path:filename>')
def static_file(filename):
    return send_from_directory('static', filename)

@app.route("/process_notes", methods = ['POST'])
@login_required
def process_notes():
    note_data = request.get_json()
    keys = note_data['notes']
    values = note_data['positions']
    notes = ""
    positions = ""
    for i in range(len(keys)):
        notes += keys[i]
        notes = "-".join(keys)
    for i in range(len(values)):
        positions += str(values[i])
        positions += "-"

    db.execute("DELETE FROM track WHERE user_ID = ?", session.get("user_id") )
    db.execute("INSERT INTO track(notes, positions, user_ID) VALUES (?, ?, ?)", notes, positions, session.get("user_id"))
    return notes, positions

@app.route("/finish_track", methods = ['POST'])
@login_required
def finish_track():
    notetrial_sql = db.execute("SELECT notes, positions FROM track WHERE user_ID = ?", session.get("user_id"))
    notetrial = notetrial_sql[0]["notes"]
    print(notetrial)
    if notetrial == "":
        return render_template("createtrack.html", error="Place some notes on the musicline to create your track")
    mood_list_sql = db.execute("SELECT mood FROM moods WHERE user_ID = ?", session.get("user_id"))
    print(mood_list_sql)
    mood_list_tmp = mood_list_sql[0]['mood']
    mood_list = mood_list_tmp.split('-')
    mood_list = [item for item in mood_list if item]
    print(f"Result list is: {mood_list}")

    return render_template('finishtrack.html', moods = mood_list)

@app.route("/save_track", methods = ['POST'])
def save_track():

    name = request.form.get("trackname")

    mood_list_sql = db.execute("SELECT mood FROM moods WHERE user_ID = ?", session.get("user_id"))
    if mood_list_sql == None:
        return render_template("index_logged.html", error="Error.")
    track_moods = mood_list_sql[0]['mood']
    notes_list_sql = db.execute("SELECT notes FROM track WHERE user_ID = ?", session.get("user_id"))
    try:
        track_notes = notes_list_sql[0]['notes']
    except IndexError:
        return render_template("index_logged.html", error="Error.")

    positions_list_sql = db.execute("SELECT positions FROM track WHERE user_ID = ?", session.get("user_id"))
    track_positions = positions_list_sql[0]['positions']

    time = datetime.datetime.now()
    db.execute("INSERT INTO tracks(user, notes, positions, moods, name, time) VALUES(?, ?, ?, ?, ?, ?)", session.get("user_id"), track_notes, track_positions, track_moods, name, time)
    db.execute("DELETE FROM track WHERE user_ID = ?", session.get("user_id"))
    db.execute("DELETE FROM moods WHERE user_ID = ?", session.get("user_id"))
    return render_template("index_logged.html", error="Track saved.")

@app.route("/trackhistory", methods = ['GET', 'POST'])
def trackhistory():
    trackname = request.args.get("trackname")
    track_data = db.execute("SELECT * FROM tracks WHERE name = ?", trackname)
    track_notes_sql = track_data[0]["notes"]
    track_positions_sql = track_data[0]["positions"]
    track_moods_sql = track_data[0]["moods"]
    track_time_sql = track_data[0]["time"]

    track_notes = track_notes_sql.split("-")
    track_notes = [item for item in track_notes if item]

    track_positions = track_positions_sql.split("-")
    track_positions = [item for item in track_positions if item]
    for i in range(len(track_positions)):
        track_positions[i] = int(track_positions[i])

    track_moods = track_moods_sql.split("-")
    track_moods = [item for item in track_moods if item]

    notes = dict(zip(track_notes, track_positions))

    print(notes)
    print(track_moods)
    return render_template("trackdisplay.html", notes = notes, moods = track_moods, name = trackname, time = track_time_sql)