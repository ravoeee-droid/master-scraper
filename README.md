# DG Master Scraper

First usable version: **live job discovery**, not yet 30-day verified hot leads.

- Uses BundesAPI's [documented unofficial Bundesagentur Jobsuche API](https://github.com/bundesAPI/jobsuche-api) directly, not a rewritten scraper.
- Real [Crawlee Python](https://github.com/apify/crawlee-python) and [Trafilatura](https://github.com/adbar/trafilatura) pip dependencies in `worker/requirements.txt`.
- [changedetection.io](https://github.com/dgtlmoon/changedetection.io) is proposed for historical monitoring, **not running yet**.
- Runs a Next.js search dashboard on Vercel. The Python worker **does not run on Vercel**.
- No historical vacancy evidence or private ownership validation exists yet. Every such field is marked unverified.

## Local
`npm install && npm run dev`

## Worker
`pip install -r worker/requirements.txt`, then `python worker/crawl.py https://example.org/karriere`.

## Required next stage
Add persistent storage, daily observation, ownership research with proofs, deduplication and tests; run the crawler on a scheduled container host. Respect access terms and applicable privacy law.
