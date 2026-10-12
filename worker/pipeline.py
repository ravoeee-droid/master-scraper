"""Scheduled evidence collector. Original Crawlee/Trafilatura are installed, not reimplemented.
Store observations in a persistent SQLite volume, or supply DATABASE_PATH.
Never promote a vacancy to 30-day-confirmed based on a single publication date.
"""
import asyncio, json, os, sqlite3, time
from datetime import datetime, timezone
from urllib.parse import urlencode
import httpx
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
import trafilatura

DB=os.getenv("DATABASE_PATH","/data/observations.sqlite3")
API="https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
REGIONS=os.getenv("REGIONS","Nordrhein-Westfalen,Bayern,Baden-Württemberg,Niedersachsen,Hessen").split(",")
KEYWORDS=os.getenv("KEYWORDS","Pflegefachkraft,Altenpfleger,examinierte Pflegefachkraft").split(",")
BLOCK=("caritas","diakonie","awo","johanniter","korian","all[oö]heim","kursana")
def now():return datetime.now(timezone.utc).isoformat()
def dbopen():
 os.makedirs(os.path.dirname(os.path.abspath(DB)),exist_ok=True)
 conn=sqlite3.connect(DB)
 conn.execute("PRAGMA journal_mode=WAL")
 conn.executescript("""
 CREATE TABLE IF NOT EXISTS jobs (
 key TEXT PRIMARY KEY,employer TEXT,title TEXT,location TEXT,source_url TEXT,
 advertised_date TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,
 observation_count INTEGER NOT NULL DEFAULT 1, last_check_status TEXT NOT NULL,
 ownership_status TEXT NOT NULL DEFAULT 'UNKNOWN', contact_status TEXT NOT NULL DEFAULT 'UNKNOWN'
 );
 CREATE TABLE IF NOT EXISTS observations (
 key TEXT NOT NULL, observed_at TEXT NOT NULL,status TEXT NOT NULL,
 source_url TEXT, PRIMARY KEY(key,observed_at)
 );
 CREATE TABLE IF NOT EXISTS runs (run_at TEXT NOT NULL, status TEXT NOT NULL, found INTEGER, error TEXT);
 """)
 return conn
def normalize(j):
 ref=str(j.get("referenznummer") or j.get("refnr") or "").strip()
 title=j.get("titel") or j.get("stellenangebotsTitel") or ""
 company=j.get("firma") or j.get("arbeitgeber") or ""
 location=j.get("arbeitsort") or {}
 if isinstance(location,dict):location=location.get("ort") or location.get("region") or ""
 return dict(key=ref,employer=str(company),title=str(title),location=str(location),
   advertised_date=j.get("aktuelleVeroeffentlichungsdatum") or j.get("veroeffentlichungsdatum"),
   source_url="https://www.arbeitsagentur.de/jobsuche/jobdetail/"+ref)
async def discover(client):
 seen={}
 for region in REGIONS:
  for keyword in KEYWORDS:
   params=dict(was=keyword,wo=region,size=100,page=1,angebotsart=1)
   try:
    r=await client.get(API,params=params,headers={"X-API-Key":"jobboerse-jobsuche"})
    r.raise_for_status()
    d=r.json()
    raw=d.get("ergebnisliste",d.get("stellenangebote",[]))
    if not isinstance(raw,list):raise ValueError("Unknown BA response schema")
    for x in raw:
     j=normalize(x)
     if j["key"] and j["title"]:seen[j["key"]]=j
   except Exception as e:print(json.dumps({"source":"BA","region":region,"keyword":keyword,"error":str(e)}),flush=True)
   await asyncio.sleep(.25)
 return list(seen.values())
async def snapshot_web(urls):
 """Optional Crawl of explicitly supplied *verified* employer career page URLs."""
 pages=[]
 if not urls:return pages
 crawler=BeautifulSoupCrawler(max_requests_per_crawl=min(25,len(urls)),max_concurrency=2)
 @crawler.router.default_handler
 async def handler(ctx:BeautifulSoupCrawlingContext):
  text=trafilatura.extract(str(ctx.soup),include_links=True) or ""
  pages.append({"url":ctx.request.url,"text":text[:12000],"checked_at":now()})
 await crawler.run(urls)
 return pages
def persist(jobs):
 conn=dbopen();timestamp=now()
 for j in jobs:
  old=conn.execute("SELECT key FROM jobs WHERE key=?",(j["key"],)).fetchone()
  if old:
   conn.execute("UPDATE jobs SET employer=?,title=?,location=?,source_url=?,advertised_date=?,last_seen=?,observation_count=observation_count+1,last_check_status='OBSERVED' WHERE key=?",
    (j["employer"],j["title"],j["location"],j["source_url"],j["advertised_date"],timestamp,j["key"]))
  else:
   conn.execute("INSERT INTO jobs(key,employer,title,location,source_url,advertised_date,first_seen,last_seen,last_check_status) VALUES(?,?,?,?,?,?,?,?,?)",
    (j["key"],j["employer"],j["title"],j["location"],j["source_url"],j["advertised_date"],timestamp,timestamp,"OBSERVED"))
  conn.execute("INSERT INTO observations(key,observed_at,status,source_url) VALUES(?,?,?,?)",(j["key"],timestamp,"OBSERVED",j["source_url"]))
 conn.execute("INSERT INTO runs(run_at,status,found,error) VALUES(?,?,?,?)",(timestamp,"OK",len(jobs),None))
 conn.commit();conn.close()
async def run_once():
 async with httpx.AsyncClient(timeout=20.0,follow_redirects=True) as client:jobs=await discover(client)
 if not jobs:
  conn=dbopen();conn.execute("INSERT INTO runs VALUES(?,?,?,?)",(now(),"NO_RESULTS",0,"No valid results; no vacancies declared closed"));conn.commit();conn.close()
  print("No jobs returned; no records marked verified.",flush=True);return
 persist(jobs)
 print(json.dumps({"observed":len(jobs),"at":now(),"database":DB}),flush=True)
async def main():
 interval=max(3600,int(os.getenv("INTERVAL_SECONDS","86400")))
 while True:
  try:await run_once()
  except Exception as e:print("RUN_FAILED",repr(e),flush=True)
  await asyncio.sleep(interval)
if __name__=="__main__":asyncio.run(main())
