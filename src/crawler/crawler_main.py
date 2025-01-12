#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import collections
import hashlib
import io
import os
import re
import sys

import aiohttp
import aiomysql
import feedparser
import loguih
from loguru import logger
# TODO: port to newspaper4k
import newspaper
import nltk
import orjson
import pymysql

CrawlerContext = collections.namedtuple("CrawlerContext", ("pool", "session"))
Feed = collections.namedtuple("Feed", ("url", "publisher", "form"))
ArticleInfo = collections.namedtuple("ArticleInfo", ("title", "publisher", "link"))

async def save_article_to_relevancy(conn: aiomysql.Connection, cur: aiomysql.Cursor, article_info: ArticleInfo, article_text: str):
    while True:
        try:
            await cur.execute("INSERT INTO CrawlerToRelevancy "
                              "(publisher, title, article_text, link) "
                              "VALUES "
                              "(%s, %s, %s, %s);",
                              (article_info.publisher, article_info.title, article_text, article_info.link))
            await conn.commit()
        except pymysql.err.OperationalError:
            await asyncio.sleep(0.25)
            continue
        except pymysql.err.IntegrityError:
            logger.warn(f"Could not send {article_info.title} to relevancy")
        break

def fix_escaped_unicode(i) -> str:
    b = []
    e = 0
    for m in re.finditer(r'\\x([0-9a-fA-F]{2})', i):
        b.append(i[e:m.start()].encode('utf-8'))
        b.append(bytes([(int(m.group(1), 16))]))
        e = m.end()
    b.append(i[e:].encode('utf-8'))
    return b''.join(b).decode('utf-8', errors='replace')

async def fetch_full_article(ctx: CrawlerContext, url: str) -> newspaper.Article:
    async with ctx.session.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
    }) as response:
        art = newspaper.Article(url)
        art.download(input_html=await response.read())
        art.parse()
        return art

async def article_seen(conn: aiomysql.Connection, cur: aiomysql.Cursor, art: ArticleInfo) -> bool:
    sha = hashlib.sha256(art.link.encode("utf-8")).hexdigest()
    await cur.execute("SELECT 1 "
                      "FROM SeenCoverage "
                      "WHERE title = %s "
                      " AND publisher = %s "
                      "LIMIT 1;",
                      (art.title, art.publisher))
    if len(await cur.fetchall()) == 1:
        return True
    while True:
        try:
            await cur.execute("INSERT INTO SeenCoverage "
                              "(title, publisher, article_url_sha256) "
                              "VALUES ( %s, %s, %s );",
                              (art.title, art.publisher, sha))
            await conn.commit()
        except pymysql.err.OperationalError:
            await asyncio.sleep(0.25)
            continue
        except pymysql.err.IntegrityError:
            return True
        break
    return False

async def feeder(ctx: CrawlerContext, feed: Feed):
    while True:
        conn = await ctx.pool.acquire()
        cur = await conn.cursor()

        match feed.form:
            case "rss" | "erss" | "rdo":
                async with ctx.session.get(feed.url, headers={
                        "User-Agent": "feedparser/6.0.11",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "application/atom+xml,application/rdf+xml,application/rss+xml,application/x-netcdf,application/xml;q=0.9,text/xml;q=0.2,*/*;q=0.1",
                        "A-Im": "feed",
                        "Connection": "close"
                }) as resp:
                    if resp.status != 200:
                        logger.error(f"error code {resp.status} for {feed.publisher}")
                    headers = dict(resp.headers)
                    headers["content-location"] = str(resp.url)
                    articles = feedparser.parse(str(await resp.read()), response_headers=headers)["entries"]
                for article in articles:
                    title = fix_escaped_unicode(article["title"])
                    article_info = ArticleInfo(title, feed.publisher, article["link"])
                    if await article_seen(conn, cur, article_info):
                        continue
                    if "description" not in article:
                        article["description"] = "No description provided."
                    if feed.form == "erss" and "content" in article:
                        article_text = "Summary: " + article["description"] + "\nText: " + article["content"][0]["value"]
                    elif feed.form == "rss" or feed.form == "erss":
                        article_text = "Summary: " + article["description"] + "\nText: " + (await fetch_full_article(ctx, article["link"])).text
                    elif feed.form == "rdo":
                        article_text = "Text: " + article["description"]
                    logger.debug(f"Read {title} from {feed.publisher}")
                    await save_article_to_relevancy(conn, cur, article_info, fix_escaped_unicode(article_text))
            case "cnn" | "maan" | "hespress" | "n3k":
                # TODO: fork newspaper3k, use async requests only
                if feed.form == "cnn":
                    articles = [article.url for article in newspaper.build("https://cnn.com").articles if (
                        ("middle" in article.url and "east" in article.url)
                        or ("world" in article.url)
                        or ("netanyahu" in article.url)
                        or ("palestine" in article.url)
                        or ("israel" in article.url)
                        or ("gaza" in article.url)
                        or ("khameini" in article.url)
                        or ("west" in article.url and "bank" in article.url)
                        or ("iran" in article.url)
                        or ("syria" in article.url)
                        or ("yemen" in article.url)
                        or ("abbas" in article.url)
                        or ("palestinian" in article.url)
                        or ("idf" in article.url)
                        or ("hamas" in article.url)
                        or ("hezbollah" in article.url)
                        or ("israeli" in article.url)
                        or ("egypt" in article.url)
                        or ("world/live-news" in article.url)
                    ) and (
                        article.url.startswith("https://cnn.com")
                        or article.url.startswith("https://cnnespanol.cnn.com")
                        or article.url.startswith("https://arabic.cnn.com")
                    )]
                elif feed.form == "maan":
                    articles = [article.url for article in newspaper.build("https://www.maannews.net").articles if article.url.endswith(".html")]
                elif feed.form == "hespress":
                    articles = [article.url for article in newspaper.build("https://www.hespress.com").articles if (
                        article.url.startswith("https://www.hespress.com")
                        or article.url.startswith("https://en.hespress.com")
                    )]
                else:
                    articles = [article.url for article in newspaper.build(feed.url).articles]
                for url in articles:
                    article = await fetch_full_article(ctx, url)
                    title = fix_escaped_unicode(article.title)
                    article_info = ArticleInfo(title, feed.publisher, url)
                    if await article_seen(conn, cur, article_info):
                        continue
                    article.nlp()
                    article_text = "Summary: " + article.summary + "\nText: " + article.text
                    logger.debug(f"Read {title} from {feed.publisher}")
                    await save_article_to_relevancy(conn, cur, article_info, fix_escaped_unicode(article_text))
            case _:
                logger.error(f"unrecognized feed type {feed.form} for publisher {feed.publisher}")
        await ctx.pool.release(conn)
        await asyncio.sleep(15)

async def main():
    # Initialization steps
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    creds = orjson.loads(open("../../secrets/db.json", "r").read())
    pool = await aiomysql.create_pool(autocommit=False, maxsize=10, **creds)
    feeds = [Feed(i["url"], i["publisher"], i["format"]) for i in orjson.loads(open("feeds.json", "r").read())]
    connector = aiohttp.TCPConnector(limit=0, resolver=aiohttp.resolver.AsyncResolver(), ssl=False)
    ctx = CrawlerContext(pool, aiohttp.ClientSession(connector=connector))
    logger.remove()
    logger.add(sys.stdout, colorize=True, format="<green>{time: YYYY-MM-DD HH:mm:ss.SSS}</green> <level>{level}</level> <b>(crawler)</b> {message}")
    loguih.setup()
    nltk.download("punkt_tab")

    _tasks = []
    for feed in feeds:
        _tasks.append(asyncio.create_task(feeder(ctx, feed)))
    await asyncio.gather(*_tasks)

if __name__ == "__main__":
    asyncio.run(main())
