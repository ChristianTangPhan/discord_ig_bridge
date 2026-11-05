"""Run once to find your IG group chat's thread ID. Also saves the login session."""
import os

from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()

ig = Client()
if os.path.exists("ig_session.json"):
    ig.load_settings("ig_session.json")
ig.login(os.environ["IG_USERNAME"], os.environ["IG_PASSWORD"])
ig.dump_settings("ig_session.json")  # relay.py reuses this session

for t in ig.direct_threads(amount=20):
    print(t.id, "|", t.thread_title, "|", [u.username for u in t.users])
