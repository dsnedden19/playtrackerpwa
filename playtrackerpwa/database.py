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


def save_game_upload(game, play_stats):
    game_id = game.get("id")
    if not game_id:
        raise ValueError("Game data must include an id.")

    with psycopg.connect(_database_url()) as connection:
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
            cursor.execute("DELETE FROM play_stats WHERE game_id = %s", (str(game_id),))

            for record in play_stats:
                record_id = record.get("id")
                if not record_id:
                    raise ValueError("Every play-stat record must include an id.")
                cursor.execute(
                    """
                    INSERT INTO play_stats (
                        id, game_id, category, play, counters, data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
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

    return len(play_stats)
