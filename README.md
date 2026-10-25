# Play Tracker

The app stores games, play statistics, and individual made/missed shot attempts
in the browser while it is offline. Use the **Upload Game** action on the Saved
Games page to push a game to a local PostgreSQL server.

## PostgreSQL setup

1. Create a database, for example:

   ```sql
   CREATE DATABASE playtracker;
   ```

2. Set `DATABASE_URL` before starting Flask. For a default local PostgreSQL
   installation:

   ```bash
   export DATABASE_URL=postgresql://postgres:your-password@localhost:5432/playtracker
   ```

3. Install dependencies and start the app:

   ```bash
   pip install -r requirements.txt
   flask --app app run
   ```

The `games`, `play_stats`, and `shots` tables are created automatically on the
first upload. Each shot row includes its court zone and 0–1000 x/y court
coordinates, result, category, type, play, and timestamp. Coordinate origin is
the lower-left corner, with Y increasing upward. Re-uploading a game updates
the game and replaces its play-stat and shot rows, so the PostgreSQL copy
matches the browser payload.
