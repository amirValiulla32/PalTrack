#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import glob
import logging
import os
import signal
import subprocess
import sys

import aiomysql
import loguih
from loguru import logger
import prctl
import orjson
import teestream

PALTRACK_MODULES = {
    "crawler",
    "gsql"
}
PALTRACK_VERSION = "0.1.0-dev"

async def main():
    # Set up environment variables
    os.environ["PALTRACK_VERSION"] = PALTRACK_VERSION

    # Set working directory to script/installation directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print(f"\n\x1b[31;1mPal\x1b[37;1mTr\x1b[32;1mack \x1b[39;1mv{PALTRACK_VERSION} bootstrap\x1b[0m\n"
          f"\x1b[37;3m(c) Copyright 2024 Amir Valiulla, Amy Parker, Dahlia Sukaik\n"
          f"Licensed under the AGPLv3 <\x1b[1m\x1b]8;;https://www.gnu.org/licenses/agpl-3.0.html\x1b\\gnu.org/licenses/agpl-3.0.html\x1b]8;;\x1b\\\x1b[0m\x1b[37m>\x1b[0m\n")

    # Set up logging facilities
    logger.remove()
    logger.add(sys.stdout, colorize=True, format="<green>{time: YYYY-MM-DD HH:mm:ss.SSS}</green> <level>{level}</level> <b>(bootstrap)</b> {message}")
    loguih.setup()
    # Split output between stdout/stderr and a file
    teestream.load_default_redirect("paltrack")

    # Load database credentials
    creds = orjson.loads(open("../secrets/db.json", "r").read())

    # Connect to and update the database
    conn = await aiomysql.connect(**creds)
    cur = await conn.cursor()
    await cur.execute("SELECT * "
                      "FROM information_schema.tables "
                      "WHERE table_schema = %s "
                      "    AND table_name = 'table_versions' "
                      "LIMIT 1;",
                      (creds["db"]))
    # getting table_versions
    if len(await cur.fetchall()) == 1:
        await cur.execute("SELECT component, version "
                          "FROM table_versions;")
        table_versions = dict(await cur.fetchall())
    else:
        await cur.execute("CREATE TABLE table_versions("
                          " component varchar(12) primary key,"
                          " version smallint not null"
                          ");")
        await conn.commit()
        table_versions = {}
    for mod in PALTRACK_MODULES:
        ver = table_versions.get(mod, 0)
        max_ver = int(sorted(glob.glob(f"{mod}/{mod}-*.sql"))[-1][-8:-4])
        for n in range(ver+1, max_ver+1):
            cmds = open(f"{mod}/{mod}-{str(n).zfill(4)}.sql", "r").read()
            for cmd in cmds.split("\n"):
                if cmd.isspace() or cmd == "":
                    continue
                await cur.execute(cmd)
        if ver == 0:
            await cur.execute("INSERT INTO table_versions "
                              "(component, version) "
                              "VALUES ( %s, %s );",
                              (mod, max_ver))
        else:
            await cur.execute("UPDATE table_versions "
                              "SET version = %s "
                              "WHERE component = %s;",
                              (max_ver, mod))
        await conn.commit()
    logger.debug(f"Successfully connected to database '{creds['db']}'")
    await cur.close()
    conn.close()

    procs = [subprocess.Popen(["python3", f"{x}/{x}_main.py"], shell=False, preexec_fn=lambda: prctl.set_pdeathsig(signal.SIGKILL)) for x in PALTRACK_MODULES]
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
