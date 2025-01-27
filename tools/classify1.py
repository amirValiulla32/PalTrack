#!/usr/bin/env python3

import os
import orjson
from hashlib import sha256
import asyncio
import aiomysql

async def connect_to_db():
    with open("../secrets/db.json") as f:
        creds = orjson.loads(f.read())
    try:
        conn = await aiomysql.connect(**creds)
        print("Database connection successful!")
        return conn
    except Exception as e:
        print(f"Error: {e}")
        return None

async def fetch_single_article(processed_hashes: set[str]):
    conn = await connect_to_db()
    if conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT article_text FROM CrawlerToRelevancy;")
                async for row in cursor:
                    article = row[0]
                    article_hash = sha256(article.encode("utf-8")).hexdigest()
                    if article_hash not in processed_hashes:
                        processed_hashes.add(article_hash)
                        # Debugging print statement to track processed hashes
                        print(f"Processed hashes count: {len(processed_hashes)}")
                        return article
                return None
        except Exception as e:
            print(f"Error fetching data: {e}")
        finally:
            conn.close()
    else:
        return None

class Getch:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def ensure_directory_exists(path):
    print(f"ensuring {path}")
    if not os.path.exists(path):
        os.makedirs(path)

DIRS = (
    "../../classifier1-data/relevant",
    "../../classifier1-data/not-relevant",
    "../../classifier1-data/dahlia"
)

async def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    [ensure_directory_exists(x) for x in DIRS]

    getch = Getch()
    processed_hashes = set()

    [processed_hashes.add(x.name) for y in DIRS for x in os.scandir(y)]

    print("\nPress the following buttons to sort the article accordingly:")
    print("a = relevant, s = not relevant, d = Dahlia, q = quit\n")

    while True:
        article = await fetch_single_article(processed_hashes)
        if article is None:
            print("No more articles found in the database. Exiting...")
            break

        print("\nNew Article:")
        print(article)

        article_hash = sha256(article.encode("utf-8")).hexdigest()
        print("256 hexdigest:", article_hash)

        while True:
            match getch():
                case "a":
                    folder_path = DIRS[0]
                case "s":
                    folder_path = DIRS[1]
                case "d":
                    folder_path = DIRS[2]
                case "q":
                    print("Exiting...")
                    exit()
                case _:
                    print("Invalid input. Please press 'a', 's', 'd', or 'q'.")

            # Save the article to the appropriate directory
            file_path = os.path.join(folder_path, article_hash)
            with open(file_path, "w+") as f:
                f.write(article)

            print(f"Saved to: {file_path}")
            break

if __name__ == "__main__":
    asyncio.run(main())
