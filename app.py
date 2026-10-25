from urllib.parse import quote

from flask import Flask, render_template, request, send_from_directory
from psycopg import Error as PsycopgError

from database import save_game_upload

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
        "2 High", "4 High","4 High Box", "5 out", "Boston", "Box", "Celtic", "Chin",
        "Duke", "Hi Low", "Jersey", "Muchilla", "Nova", "NY",
        "Oregon", "Power", "Rub", "Texas", "Through", "Transition"
    ],
    "Zone Offense": [
        "14", "32", "5 out","Chin", "Hi Low", "Hope", "Michigan", "NY", "Power", "Sparkle", "Triangle"
    ],
    "Blob": [
        "Box", "K", "L", "O", "Strong", "Weak", "Weak Rev", "X"
    ],
    "Slob": [
        "Atlanta", "Irish", "Slice", "Vegas"
    ],
    "Defense": [
        "1", "2-high", "Shakers", "Tri and 2", "Transition",
        "1-3-1", "3-2", "2-3", "2-high-3", "2-high-2",
        "Marquette", "Twilight"
    ]
}

selector_config = {
    "Offense": {
        "Man": {"category": "Man Offense", "plays": plays_by_category["Man Offense"]},
        "Zone": {"category": "Zone Offense", "plays": plays_by_category["Zone Offense"]},
        "BLOB": {"category": "Blob", "plays": plays_by_category["Blob"]},
        "SLOB": {"category": "Slob", "plays": plays_by_category["Slob"]},
    },
    "Defense": {
        "Man": {
            "category": "Defense",
            "plays": ["1", "2-high", "Shakers", "Tri and 2", "Transition"],
        },
        "Zone": {
            "category": "Defense",
            "plays": ["1-3-1", "3-2", "2-3", "2-high-3", "2-high-2", "Marquette", "Twilight"],
        },
    },
}

offense_counters = [
    "LUM", "LUA", "UnCon LUM", "UnCon LUA",
    "MidM", "MidA", "3ptM", "3ptA", "FTM", "FTA",
    "O Reb", "2nd Chance", "D Foul", "O Foul", "Turnover", "Ran"
]

defense_counters = [
    "Off Reb", "2nd Chance Pts", "D Reb", "D Foul",
    "FTM", "FTA", "O Foul", "Tip", "Turnover", "Close Out",
    "Points", "Ran"
]


# -------------------------
# STAT ENTRY PAGE
# -------------------------
@app.route("/stat/<cat>/<play>", methods=["GET", "POST"])
def stat(cat, play):
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

        return render_template(
            "category.html",
            selector_config=selector_config,
            offense_counters=offense_counters,
            defense_counters=defense_counters,
        )

    return render_template("setup.html")


# -------------------------
# CATEGORY PAGE
# -------------------------
@app.route("/category")
def category():
    return render_template(
        "category.html",
        selector_config=selector_config,
        offense_counters=offense_counters,
        defense_counters=defense_counters,
    )


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
    shots = payload.get("shots", [])

    if not isinstance(game, dict):
        return {
            "success": False,
            "message": "Game data is missing."
        }, 400

    if play_stats is None:
        return {
            "success": False,
            "message": "Play-stat data is missing."
        }, 400

    if not isinstance(play_stats, list) or not all(
        isinstance(record, dict) for record in play_stats
    ):
        return {
            "success": False,
            "message": "Play-stat data must be a list of objects."
        }, 400

    if not isinstance(shots, list) or not all(
        isinstance(shot, dict) for shot in shots
    ):
        return {
            "success": False,
            "message": "Shot data must be a list of objects."
        }, 400

    try:
        upload_counts = save_game_upload(game, play_stats, shots)
    except (RuntimeError, ValueError) as error:
        return {
            "success": False,
            "message": str(error)
        }, 503 if isinstance(error, RuntimeError) else 400
    except PsycopgError:
        app.logger.exception("Could not save game upload to PostgreSQL.")
        return {
            "success": False,
            "message": "Could not save game to PostgreSQL."
        }, 503

    return {
        "success": True,
        "message": "Game saved to PostgreSQL.",
        "gameId": game.get("id"),
        **upload_counts
    }, 200


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
