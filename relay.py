"""Two-way relay between one Instagram group chat and one Discord channel."""
import asyncio
import os

import aiohttp
import discord
from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()  # reads .env in the current folder into os.environ

# ---- Config (from .env) ----
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
IG_USER = os.environ["IG_USERNAME"]
IG_PASS = os.environ["IG_PASSWORD"]
IG_THREAD_ID = os.environ["IG_THREAD_ID"]
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "15"))  # don't go much lower or IG gets suspicious
SESSION_FILE = "ig_session.json"  # reusing a session avoids repeated logins

# ---- Instagram side (instagrapi is synchronous/blocking) ----
ig = Client()
seen_ids = set()  # IG message IDs we've already handled
user_cache = {}   # user_id -> (username, avatar_url)


def ig_login():
    if os.path.exists(SESSION_FILE):
        ig.load_settings(SESSION_FILE)
    ig.login(IG_USER, IG_PASS)
    ig.dump_settings(SESSION_FILE)


def ig_get_new_messages():
    msgs = ig.direct_messages(IG_THREAD_ID, amount=20)  # newest first
    new = [m for m in msgs if m.id not in seen_ids]
    seen_ids.update(m.id for m in new)
    new.reverse()  # oldest first, so Discord shows them in order
    # skip our own bot account's messages (prevents echo loops) and non-text
    return [m for m in new if str(m.user_id) != str(ig.user_id) and m.text]


def ig_user(user_id):
    if user_id not in user_cache:
        info = ig.user_info(user_id)
        user_cache[user_id] = (info.username, str(info.profile_pic_url))
    return user_cache[user_id]


# ---- Discord side ----
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
poller_started = False


@bot.event
async def on_ready():
    global poller_started
    print(f"Discord: logged in as {bot.user}")
    if not poller_started:  # on_ready can fire again on reconnect
        poller_started = True
        asyncio.create_task(poll_instagram())


@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    if message.author.bot or message.webhook_id:  # ignore bots + our own webhook
        return
    if not message.content:
        return
    text = f"[{message.author.display_name}] {message.content}"
    # run the blocking IG call in a thread so it doesn't freeze the bot
    await asyncio.to_thread(ig.direct_send, text, thread_ids=[int(IG_THREAD_ID)])


async def poll_instagram():
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)

        # mark existing history as seen so we don't dump old messages on startup
        await asyncio.to_thread(ig_get_new_messages)
        print("Instagram: polling started")

        while True:
            try:
                for m in await asyncio.to_thread(ig_get_new_messages):
                    name, pic = await asyncio.to_thread(ig_user, m.user_id)
                    await webhook.send(
                        m.text,
                        username=f"{name} (IG)",
                        avatar_url=pic,
                        allowed_mentions=discord.AllowedMentions.none(),  # no @everyone from IG
                    )
            except Exception as e:
                print("IG poll error:", e)
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    ig_login()
    bot.run(DISCORD_TOKEN)
