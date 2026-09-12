# Play Tracker

The app stores games and individual play events in the browser while it is offline. Use
the **Upload Game** action on the Saved Games page to push a game to a local
PostgreSQL server.

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

The `games` and `game_events` tables are created automatically on the first
upload. Each recorded action is stored as one ordered event row with a unique
`event_number` within its game. Re-uploading a game replaces its event rows so
the PostgreSQL copy matches the browser payload.
