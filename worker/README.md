# Persistent observation worker

Deploy using Railway or another always-on Docker host with a persistent volume mounted at `/data`.

Uses original PyPI versions of Crawlee, Trafilatura and HTTPX from requirements.txt. No homebuilt versions of those libraries.

Tracks first/last seen and records every successful source observation. An older advertised date is NOT proof of a continuously unfilled vacancy. Neither is a pair of observations 30 days apart, unless intervening availability is independently checked. The worker does not currently confirm ownership, actual job-site status, or decision-maker identity.

Env: `DATABASE_PATH=/data/observations.sqlite3`, `INTERVAL_SECONDS=86400`, `REGIONS`, `KEYWORDS`.

Railway account currently cannot provision another project under its free plan. Deploying the worker requires capacity and a persistent volume. No worker has been activated automatically.
