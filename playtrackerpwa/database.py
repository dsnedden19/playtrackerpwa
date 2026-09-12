import os

import psycopg
from psycopg.types.json import Jsonb


def _database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it to your local PostgreSQL connection string."
        )
    return database_url


def save_game_upload(game, events):
    game_id = game.get("id")
    if not game_id:
        raise ValueError("Game data must include an id.")

    with psycopg.connect(_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'games'
                  AND column_name = 'id'
                """
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "ALTER TABLE IF EXISTS games RENAME TO games_legacy"
                )
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
                CREATE TABLE IF NOT EXISTS game_events (
                    id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                    event_number INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    play TEXT NOT NULL,
                    stat TEXT NOT NULL,
                    shot_location JSONB,
                    data JSONB NOT NULL,
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (game_id, event_number)
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
            cursor.execute("DELETE FROM game_events WHERE game_id = %s", (str(game_id),))

            for record in events:
                record_id = record.get("id")
                if not record_id:
                    raise ValueError("Every event must include an id.")
                cursor.execute(
                    """
                    INSERT INTO game_events (
                        id, game_id, event_number, event_type, category, play,
                        stat, shot_location, data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(record_id),
                        str(game_id),
                        record.get("eventNumber"),
                        record.get("eventType", "offense"),
                        record.get("category", ""),
                        record.get("play", ""),
                        record.get("stat", ""),
                        Jsonb(record["shotLocation"])
                        if record.get("shotLocation") else None,
                        Jsonb(record),
                    ),
                )

    return len(events)
