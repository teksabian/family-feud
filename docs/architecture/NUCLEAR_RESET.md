# Nuclear Reset on Startup

**Since:** v1.0.5

---

## What It Does

Every time the server starts (`python app.py` or Render restart):

1. All submissions deleted
2. All rounds deleted
3. All team names cleared
4. All codes reset to unused
5. All old sessions invalidated

**No data persists across restarts. Fresh slate every time.**

## How It Works

On server startup:
1. `init_db()` creates tables if needed
2. `nuke_all_data()` deletes everything
3. Fresh `STARTUP_ID` generated (microsecond timestamp)
4. All old sessions become invalid

## Session Invalidation

Each server start generates a unique `STARTUP_ID`:
- Stored in team sessions on join: `session['startup_id'] = STARTUP_ID`
- Checked on every request via `team_session_valid` decorator
- Mismatch = `session.clear()` + redirect to join page with message "Server restarted. Please join again."

## What the Database Stores (During a Session)

- Team codes (reset to unused on startup)
- Settings (registration open/closed, broadcast message)
- Current game data (deleted on startup)

## Behavior Summary

| Action | Result |
|--------|--------|
| Start server | Nuclear reset, fresh state |
| During a game | Data persists normally |
| Restart mid-game | Everything gone, teams must rejoin |
| Deploy on Render | Render rebuilds = restart = nuclear reset |

## Why This Design

The app is designed for pub trivia nights — each game night is a fresh session. There's no need to persist data between server restarts. This eliminates ghost sessions, stale data, and code collisions.
