#════════════════════════════════════════════════════════
# Spotify Lyrics Bot for ESP32 Credits to EkiZR. 
# Forked by A-flp
#════════════════════════════════════════════════════════
import os
from dotenv import load_dotenv
import discord
import asyncio
import time
import json
import re
import logging
import urllib.parse
import urllib.request

from aiohttp import web, ClientSession
from dataclasses import dataclass, field
from typing import List, Dict

load_dotenv()

# ════════════════════════════════════════════════════════
#  CONFIGURATION (Modified to use os.load_dotenv for better error handling)
# ════════════════════════════════════════════════════════
BOT_TOKEN   = os.getenv("BOT_TOKEN") # Replace with your actual bot token or set in .env
USER_ID     = int(os.getenv("USER_ID")) # Replace with the actual user ID you want to track or set in .env
PORT        = int(os.getenv("PORT")) # Replace with your desired port or set in .env
LYRIC_LEAD  = float(os.getenv("LYRIC_LEAD")) # Replace with your desired lyric lead time in seconds or set in .env

WATCHDOG_INTERVAL = 2
CACHE_LIMIT = 100
# ════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(message)s"
)

log = logging.getLogger("spotify-server")

# ════════════════════════════════════════════════════════
# GLOBALS
# ════════════════════════════════════════════════════════
http_session: ClientSession | None = None
tracked_member = None

LRC_REGEX = re.compile(r'\[(\d+):(\d+\.\d+)\](.*)')

# ════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════
@dataclass(slots=True)
class LyricLine:
    time: float
    text: str


@dataclass(slots=True)
class LyricsState:
    key: str = ""
    lines: List[LyricLine] = field(default_factory=list)
    duration: float = 0


@dataclass(slots=True)
class TrackState:
    playing: bool = False
    title: str = ""
    artist: str = ""
    album: str = ""
    start_epoch: float = 0
    end_epoch: float = 0
    duration_ms: int = 0


current = TrackState()
lyrics = LyricsState()

lyrics_cache: Dict[str, LyricsState] = {}

# ════════════════════════════════════════════════════════
# LYRICS FETCH (ASYNC)
# ════════════════════════════════════════════════════════
async def fetch_lyrics(artist: str, title: str) -> LyricsState:

    key = f"{artist}|{title}"

    cached = lyrics_cache.get(key)
    if cached:
        return cached

    url = (
        "https://lrclib.net/api/get"
        f"?artist_name={urllib.parse.quote(artist)}"
        f"&track_name={urllib.parse.quote(title)}"
    )

    for _ in range(3):

        try:

            async with http_session.get(url) as res:

                data = await res.json()

            synced = data.get("syncedLyrics") or ""
            plain = data.get("plainLyrics") or ""
            duration = data.get("duration", 0)

            lines = []

            if synced:

                for line in synced.split("\n"):

                    m = LRC_REGEX.match(line)

                    if m:
                        secs = int(m.group(1)) * 60 + float(m.group(2))
                        text = m.group(3).strip()

                        if text:
                            lines.append(LyricLine(secs, text))

            elif plain:

                for line in plain.split("\n"):

                    line = line.strip()

                    if line:
                        lines.append(LyricLine(0, line))

            state = LyricsState(key, lines, duration)

            if len(lyrics_cache) > CACHE_LIMIT:
                lyrics_cache.pop(next(iter(lyrics_cache)))

            lyrics_cache[key] = state

            log.info(f"lyrics loaded {len(lines)} lines")

            return state

        except Exception as e:
            log.warning(f"lrclib retry: {e}")
            await asyncio.sleep(1)

    return LyricsState()

# ════════════════════════════════════════════════════════
# LYRIC LOOKUP (FAST BINARY SEARCH)
# ════════════════════════════════════════════════════════
def get_lyric(progress_secs: float):

    lines = lyrics.lines
    duration = lyrics.duration

    if not lines:
        return "", "", ""

    if lines[0].time == 0:

        total = duration or 200

        idx = min(
            int((progress_secs / total) * len(lines)),
            len(lines) - 1
        )

        prev = lines[idx - 1].text if idx > 0 else ""
        curr = lines[idx].text
        nxt = lines[idx + 1].text if idx + 1 < len(lines) else ""

        return prev, curr, nxt

    lo = 0
    hi = len(lines) - 1

    while lo <= hi:

        mid = (lo + hi) // 2

        if lines[mid].time <= progress_secs:
            lo = mid + 1
        else:
            hi = mid - 1

    idx = max(0, lo - 1)

    prev = lines[idx - 1].text if idx > 0 else ""
    curr = lines[idx].text
    nxt = lines[idx + 1].text if idx + 1 < len(lines) else ""

    return prev, curr, nxt


# ════════════════════════════════════════════════════════
# DISCORD CLIENT
# ════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.presences = True
intents.members = True


class SpotifyClient(discord.Client):

    async def setup_hook(self):

        global http_session

        http_session = ClientSession()

        self.loop.create_task(spotify_watchdog())

        log.info("watchdog started")


bot = SpotifyClient(intents=intents)

# ════════════════════════════════════════════════════════
# READY
# ════════════════════════════════════════════════════════
@bot.event
async def on_ready():

    global tracked_member

    log.info(f"logged in as {bot.user}")

    for guild in bot.guilds:

        member = guild.get_member(USER_ID)

        if member:
            tracked_member = member
            break

    log.info("member cached")


# ════════════════════════════════════════════════════════
# PRESENCE UPDATE
# ════════════════════════════════════════════════════════
@bot.event
async def on_presence_update(before, after):

    if after.id != USER_ID:
        return

    await process_spotify(after)


async def process_spotify(member):

    spotify = next(
        (a for a in member.activities if isinstance(a, discord.Spotify)),
        None
    )

    if not spotify:

        current.playing = False
        return

    artist = ", ".join(spotify.artists)
    title = spotify.title

    key = f"{artist}|{title}"

    if lyrics.key != key:

        state = await fetch_lyrics(artist, title)

        lyrics.key = state.key
        lyrics.lines = state.lines
        lyrics.duration = state.duration

    current.playing = True
    current.title = title
    current.artist = artist
    current.album = spotify.album

    current.start_epoch = spotify.start.timestamp()
    current.end_epoch = spotify.end.timestamp()

    current.duration_ms = int(
        (spotify.end - spotify.start).total_seconds() * 1000
    )

# ════════════════════════════════════════════════════════
# WATCHDOG
# ════════════════════════════════════════════════════════
async def spotify_watchdog():

    await bot.wait_until_ready()

    while True:

        try:

            if tracked_member:

                await process_spotify(tracked_member)

        except Exception as e:

            log.error(f"watchdog error {e}")

        await asyncio.sleep(WATCHDOG_INTERVAL)

# ════════════════════════════════════════════════════════
# HTTP API
# ════════════════════════════════════════════════════════
async def handle_now_playing(request):

    if not current.playing:

        return web.json_response({"playing": False})

    now = time.time()

    pos_ms = int((now - current.start_epoch) * 1000)

    pos_secs = pos_ms / 1000 + LYRIC_LEAD

    prev, curr, nxt = get_lyric(pos_secs)

    return web.json_response({
        "playing": True,
        "title": current.title,
        "artist": current.artist,
        "position_ms": pos_ms,
        "duration_ms": current.duration_ms,
        "lyric_prev": prev,
        "lyric_curr": curr,
        "lyric_next": nxt
    })


async def handle_debug(request):

    return web.json_response({
        "current": vars(current),
        "lyrics_lines": len(lyrics.lines),
        "cache": len(lyrics_cache)
    })


async def handle_health(request):

    return web.json_response({
        "status": "ok",
        "time": time.time()
    })

# ════════════════════════════════════════════════════════
# SERVER
# ════════════════════════════════════════════════════════
async def start_server():

    app = web.Application()

    app.router.add_get("/now-playing", handle_now_playing)
    app.router.add_get("/debug", handle_debug)
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)

    await site.start()

    log.info(f"http server running :{PORT}")

# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════
async def main():

    await start_server()

    await bot.start(BOT_TOKEN)


if __name__ == "__main__":

    asyncio.run(main())