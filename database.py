import os
import urllib.parse

import psycopg
from psycopg.types.json import Jsonb


def _database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it to your local PostgreSQL connection string."
        )
    return database_url


def _url_with_connect_timeout(url, timeout=5):
    # Add a short connect_timeout to the DSN if not already present so
    # psycopg.connect fails fast instead of hanging until the process is
    # killed by Gunicorn's worker timeout.
    if "connect_timeout" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}connect_timeout={timeout}"


def save_game_upload(game, play_stats, shots=None):
    game_id = game.get("id")
    if not game_id:
        raise ValueError("Game data must include an id.")
    shots = shots or []

    url = _database_url()
    url_with_timeout = _url_with_connect_timeout(url, timeout=5)

    try:
        with psycopg.connect(url_with_timeout) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS games (
                        id TEXT PRIMARY KEY,
                        opponent TEXT,
                        game_date TEXT,
                        homeaway TEXT,
                        data JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS play_stats (
                        id TEXT PRIMARY KEY,
                        game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                        category TEXT NOT NULL,
                        play TEXT NOT NULL,
                        counters JSONB NOT NULL,
                        data JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shots (
                        id TEXT PRIMARY KEY,
                        game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                        category TEXT NOT NULL,
                        type TEXT NOT NULL,
                        play TEXT NOT NULL,
                        zone TEXT NOT NULL,
                        result TEXT NOT NULL CHECK (result IN ('made', 'missed')),
                        recorded_at TIMESTAMPTZ NOT NULL,
                        data JSONB NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO games (id, opponent, game_date, homeaway, data)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        opponent = EXCLUDED.opponent,
                        game_date = EXCLUDED.game_date,
                        homeaway = EXCLUDED.homeaway,
                        data = EXCLUDED.data,
                        updated_at = NOW()
                    """,
                    (
                        str(game_id),
                        game.get("opponent"),
                        game.get("date"),
                        game.get("homeaway"),
                        Jsonb(game),
                    ),
                )
                # Remove any previous play_stats for this game before re-inserting
                cursor.execute("DELETE FROM play_stats WHERE game_id = %s", (str(game_id),))
                cursor.execute("DELETE FROM shots WHERE game_id = %s", (str(game_id),))

                for record in play_stats:
                    record_id = record.get("id")
                    if not record_id:
                        raise ValueError("Every play-stat record must include an id.")

                    try:
                        cursor.execute(
                            """
                            INSERT INTO play_stats (
                                id, game_id, category, play, counters, data
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                game_id = EXCLUDED.game_id,
                                category = EXCLUDED.category,
                                play = EXCLUDED.play,
                                counters = EXCLUDED.counters,
                                data = EXCLUDED.data,
                                updated_at = NOW()
                            """,
                            (
                                str(record_id),
                                str(game_id),
                                record.get("category", ""),
                                record.get("play", ""),
                                Jsonb(record.get("counters", {})),
                                Jsonb(record),
                            ),
                        )
                    except Exception as rec_e:
                        # Surface which record failed to insert to aid debugging.
                        # Don't include full DB credentials or large payloads in the
                        # error message; include just the record id and the error.
                        raise RuntimeError(f"Failed inserting play_stat id={record_id}: {rec_e}") from rec_e

                for shot in shots:
                    shot_id = shot.get("id")
                    if not shot_id:
                        raise ValueError("Every shot record must include an id.")
                    if shot.get("result") not in ("made", "missed"):
                        raise ValueError(f"Shot id={shot_id} has an invalid result.")
                    if not all(shot.get(field) for field in (
                        "category", "type", "play", "zone", "recordedAt"
                    )):
                        raise ValueError(
                            f"Shot id={shot_id} is missing required shot details."
                        )

                    cursor.execute(
                        """
                        INSERT INTO shots (
                            id, game_id, category, type, play, zone,
                            result, recorded_at, data
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(shot_id),
                            str(game_id),
                            shot.get("category", ""),
                            shot.get("type", ""),
                            shot.get("play", ""),
                            shot.get("zone", ""),
                            shot["result"],
                            shot.get("recordedAt"),
                            Jsonb(shot),
                        ),
                    )

    except Exception as e:
        # If this is a connection/operational error, convert to a clearer
        # RuntimeError so the Flask handler will return a 503 with a helpful
        # message instead of letting Gunicorn hit a worker timeout.
        is_conn_error = False
        try:
            if hasattr(psycopg, "errors") and isinstance(e, psycopg.errors.OperationalError):
                is_conn_error = True
        except Exception:
            # If anything goes wrong checking the type, fall back to treating
            # it as a generic exception.
            is_conn_error = False

        if is_conn_error:
            try:
                parsed = urllib.parse.urlparse(url)
                host = parsed.hostname or "<unknown>"
                dbname = parsed.path.lstrip("/") or "<unknown>"
            except Exception:
                host = "<unknown>"
                dbname = "<unknown>"

            raise RuntimeError(f"Could not connect to PostgreSQL at {host}/{dbname}: {e}") from e

        # Re-raise other exceptions (ValueError for missing ids will bubble up)
        raise

    return {"playStatCount": len(play_stats), "shotCount": len(shots)}
