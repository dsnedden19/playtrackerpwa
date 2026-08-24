from flask import Flask, render_template, request, send_from_directory

@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js")

app = Flask(__name__)

# -------------------------
# PLAY DATA
# -------------------------
plays_by_category = {
    "Man Offense": [
        "2 High","4 High","5 out","Boston","Box","Celtic","Chin","Duke",
        "Hi Low","Jersey","Muchilla","Nova","NY","Oregon","Power","Rub",
        "Texas","Through","Transition"
    ],
    "Zone Offense": [
        "14","32","5 out","Hi Low","Michigan","NY","Sparkle"
    ],
    "Blob": [
        "Box","Strong","L","Weak","O","X","K"
    ],
    "Slob": [
        "Irish","Atlanta"
    ],
    "Defense": [
        "Man","3-2 Zone","2-3 Zone","Tri and 2",
        "2-3 High Man","2-3 High 3-2","2-3 High 2-3",
        "Twilight","Marquette","Transition"
    ]
}

# -------------------------
# STAT ENTRY PAGE
# -------------------------
@app.route("/stat/<cat>/<play>", methods=["GET", "POST"])
def stat(cat, play):
    # Choose counters based on category
    offense_counters = [
        "LUM","LUA","UnCon LUM","UnCon LUA",
        "MidM","MidA","3ptM","3ptA","FTM", "FTA", "O Reb","2nd Chance",
        "D Foul", "O Foul","Turnover", "Ran"
    ]

    defense_counters = [
        "Off Reb","2nd Chance","D Reb","D Foul",
        "FTM","FTA","O Foul","Tip","Turnover","Clost Out", "Ran"
    ]

    counters = defense_counters if cat == "Defense" else offense_counters

    # Initialize stats storage
    global stats
    if "stats" not in globals():
        stats = {}

    if cat not in stats:
        stats[cat] = {}

    if play not in stats[cat]:
        stats[cat][play] = {c: 0 for c in counters}

    # Handle button clicks
    if request.method == "POST":
        counter_clicked = request.form["counter"]
        stats[cat][play][counter_clicked] += 1

    return render_template(
        "stat.html",
        category=cat,
        play=play,
        counters=counters,
        values=stats[cat][play]
    )


# -------------------------
# HOME PAGE
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")

# -------------------------
# SETUP PAGE
# -------------------------
@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        opponent = request.form["opponent"]
        date = request.form["date"]
        homeaway = request.form["homeaway"]

        global game_info
        game_info = {
            "opponent": opponent,
            "date": date,
            "homeaway": homeaway
        }

        return render_template("category.html")

    return render_template("setup.html")

# -------------------------
# CATEGORY PAGE
# -------------------------
@app.route("/category")
def category():
    return render_template("category.html")

# -------------------------
# PLAYS PAGE
# -------------------------
@app.route("/plays/<cat>")
def plays(cat):
    play_list = plays_by_category.get(cat, [])
    return render_template("plays.html", category=cat, plays=play_list)


# -------------------------
# SUMMARY PAGE
# -------------------------
@app.route("/summary")
def summary():
    return render_template("summary.html", game=None, stats={})


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)


