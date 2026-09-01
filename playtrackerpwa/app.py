from urllib.parse import quote

from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js")


@app.route("/saved_games")
def saved_games():
    return render_template("saved_games.html")


# -------------------------
# PLAY DATA
# -------------------------
plays_by_category = {
    "Man Offense": [
        "2 High", "4 High", "5 out", "Boston", "Box", "Celtic", "Chin",
        "Duke", "Hi Low", "Jersey", "Muchilla", "Nova", "NY",
        "Oregon", "Power", "Rub", "Texas", "Through", "Transition"
    ],
    "Zone Offense": [
        "14", "32", "5 out", "Hi Low", "Michigan", "NY", "Sparkle"
    ],
    "Blob": [
        "Box", "Strong", "L", "Weak", "O", "X", "K"
    ],
    "Slob": [
        "Irish", "Atlanta"
    ],
    "Defense": [
        "Man", "3-2 Zone", "2-3 Zone", "Tri and 2",
        "2-3 High Man", "2-3 High 3-2", "2-3 High 2-3",
        "Twilight", "Marquette", "Transition"
    ]
}


# -------------------------
# STAT ENTRY PAGE
# -------------------------
@app.route("/stat/<cat>/<play>", methods=["GET", "POST"])
def stat(cat, play):

    offense_counters = [
        "LUM","LUA","UnCon LUM","UnCon LUA",
        "MidM","MidA","3ptM","3ptA","FTM","FTA",
        "O Reb","2nd Chance",
        "D Foul","O Foul","Turnover","Ran"
    ]

    defense_counters = [
        "Off Reb","2nd Chance","D Reb","D Foul",
        "FTM","FTA","O Foul","Tip",
        "Turnover","Clost Out","Ran"
    ]

    counters = defense_counters if cat == "Defense" else offense_counters

    global stats
    if "stats" not in globals():
        stats = {}

    if cat not in stats:
        stats[cat] = {}

    if play not in stats[cat]:
        stats[cat][play] = {c: 0 for c in counters}

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
# OFFLINE URL LIST (for the service worker to precache)
# -------------------------
@app.route("/api/offline-urls")
def offline_urls():
    urls = []
    for cat, plays in plays_by_category.items():
        urls.append(f"/plays/{quote(cat)}")
        for play in plays:
            urls.append(f"/stat/{quote(cat)}/{quote(play)}")
    return {"urls": urls}


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

    return render_template(
        "plays.html",
        category=cat,
        plays=play_list
    )


# -------------------------
# SUMMARY PAGE
# -------------------------
@app.route("/summary")
def summary():
    return render_template("summary.html", game=None, stats={})


# -------------------------
# Upload
# -------------------------
@app.route("/api/upload-game", methods=["POST"])
def upload_game():

    payload = request.get_json(silent=True)

    if not payload:
        return {
            "success": False,
            "message": "No JSON payload received."
        }, 400

    game = payload.get("game")
    play_stats = payload.get("playStats")

    if not game:
        return {
            "success": False,
            "message": "Game data is missing."
        }, 400

    if play_stats is None:
        return {
            "success": False,
            "message": "Play-stat data is missing."
        }, 400

    print("Upload received:")
    print("Game ID:", game.get("id"))
    print("Opponent:", game.get("opponent"))
    print("Play-stat records:", len(play_stats))

    return {
        "success": True,
        "message": "Upload received by Flask.",
        "gameId": game.get("id"),
        "playStatCount": len(play_stats)
    }, 200


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)


