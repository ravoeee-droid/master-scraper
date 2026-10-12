"""Uses the REAL Crawlee and Trafilatura packages, not copied implementations.
Run outside Vercel on a scheduled persistent worker; no claims about 30d history.
"""
import asyncio, json, sys
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
import trafilatura

async def main(urls):
    crawler=BeautifulSoupCrawler(max_requests_per_crawl=min(len(urls),100),max_concurrency=3)
    @crawler.router.default_handler
    async def handle(ctx: BeautifulSoupCrawlingContext):
        html=str(ctx.soup)
        text=trafilatura.extract(html,include_links=True) or ctx.soup.get_text(' ',strip=True)
        await ctx.push_data({'source_url':ctx.request.url,'text':text[:25000], 'verification':'UNVERIFIED'})
    await crawler.run(urls)
    for item in await crawler.get_data():
        print(json.dumps(item,ensure_ascii=False))
if __name__=='__main__':
    if len(sys.argv)<2:raise SystemExit('usage: python crawl.py https://example.org/karriere')
    asyncio.run(main(sys.argv[1:]))
