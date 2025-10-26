#!/usr/bin/env python3
"""
Twitter Automation Script (Bearer Token version)
------------------------------------------------
- Reads posts from post.txt (multi-line inside "")
- Posts 17/day → 8 normal tweets + 9 influencer replies
- Waits 24h after each day
- Saves URLs to normal_posts.txt and influencer_posts.txt
"""

import tweepy
import os
import time
import random
import re
from threading import Thread
from flask import Flask

# ====== CONFIG ======
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAAALU24QEAAAAA%2BJgMXUnzs6YRb2w5iEw4E%2FXtgkM%3DVThVeUHqvPH4EAyEqXdTLYzlfOXD8bPBwoCx52xkflPJyf8Nop"
ACCESS_TOKEN = "1917680783331930112-VFp1mvpIqq5xYfxBbG3IiWLPbCJrc9"
ACCESS_SECRET = "TjIVuZrh0Re7KdkCCsKwuUtTmFSU18UNvuq4tBxSHhh3h"
API_KEY = "OwRbI9wi8eglE4yAxeiJgdtBr"
API_SECRET = "HenKDXkitpno7Ciiql1FWuq1aDVuGamocqu2gswHfDMe7j6qjk"

POST_FILE = "post.txt"
INFLUENCERS_FILE = "influencers.txt"
IMAGES_FOLDER = "images"
NORMAL_OUT = "normal_posts.txt"
INFLUENCER_OUT = "influencer_posts.txt"

POSTS_PER_DAY = 17
SLEEP_BETWEEN_POSTS = 60  # seconds
WAIT_BETWEEN_DAYS = 24 * 3600  # 24 hours

# ====== SETUP ======
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)
api_v1 = tweepy.API(tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET))

# ====== HELPERS ======
def load_posts(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    posts = re.findall(r'"(.*?)"', content, re.DOTALL)
    return [p.strip() for p in posts if p.strip()]

def save_remaining_posts(path, remaining):
    with open(path, "w", encoding="utf-8") as f:
        for p in remaining:
            f.write(f'"{p.strip()}"\n\n')

def load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def save_line(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def pick_random_image():
    if not os.path.exists(IMAGES_FOLDER):
        return None
    imgs = [os.path.join(IMAGES_FOLDER, f) for f in os.listdir(IMAGES_FOLDER)
            if os.path.isfile(os.path.join(IMAGES_FOLDER, f))]
    if not imgs:
        return None
    return random.choice(imgs)

def upload_image(image_path):
    try:
        media = api_v1.media_upload(image_path)
        return media.media_id_string
    except Exception as e:
        print("⚠️ Image upload failed:", e)
        return None

def post_tweet(text, image_path=None):
    try:
        media_id = upload_image(image_path) if image_path else None
        if media_id:
            tweet = client.create_tweet(text=text, media_ids=[media_id])
        else:
            tweet = client.create_tweet(text=text)
        tweet_id = tweet.data["id"]
        return f"https://x.com/i/web/status/{tweet_id}"
    except Exception as e:
        print("❌ Error posting tweet:", e)
        return None

def get_latest_tweet_id(handle):
    try:
        tweets = client.get_users_tweets(id=client.get_user(username=handle).data.id, max_results=5)
        if tweets and tweets.data:
            return tweets.data[0].id
    except Exception as e:
        print(f"⚠️ Failed to fetch tweet for {handle}: {e}")
    return None

def reply_to_tweet(tweet_id, text, image_path=None):
    try:
        media_id = upload_image(image_path) if image_path else None
        if media_id:
            tweet = client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id, media_ids=[media_id])
        else:
            tweet = client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
        tweet_id = tweet.data["id"]
        return f"https://x.com/i/web/status/{tweet_id}"
    except Exception as e:
        print("❌ Error replying:", e)
        return None

# ====== MAIN LOOP ======
def main():
    while True:
        posts = load_posts(POST_FILE)
        if not posts:
            print("✅ All posts completed!")
            break

        influencers = load_lines(INFLUENCERS_FILE)
        if not influencers:
            print("⚠️ influencers.txt is empty.")
            break

        daily_posts = posts[:POSTS_PER_DAY]
        remaining_posts = posts[POSTS_PER_DAY:]
        half = POSTS_PER_DAY // 2

        normal_posts = daily_posts[:half]
        influencer_posts = daily_posts[half:]

        print(f"🚀 Starting new day with {len(daily_posts)} posts...")

        for text in normal_posts:
            img = pick_random_image()
            url = post_tweet(text, img)
            if url:
                print(f"✅ Normal tweet: {url}")
                save_line(NORMAL_OUT, url)
            time.sleep(SLEEP_BETWEEN_POSTS)

        for text in influencer_posts:
            handle = random.choice(influencers).lstrip("@").strip()
            tweet_id = get_latest_tweet_id(handle)
            if not tweet_id:
                print(f"⚠️ No tweet for @{handle}, skipping.")
                continue
            img = pick_random_image()
            url = reply_to_tweet(tweet_id, text, img)
            if url:
                print(f"💬 Reply to @{handle}: {url}")
                save_line(INFLUENCER_OUT, url)
            time.sleep(SLEEP_BETWEEN_POSTS)

        save_remaining_posts(POST_FILE, remaining_posts)
        print(f"✅ Removed {POSTS_PER_DAY} posts from post.txt")
        print("🌙 Waiting 24 hours...")
        time.sleep(WAIT_BETWEEN_DAYS)

# ====== DUMMY WEB SERVER ======
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Twitter automation bot is running!"

def run_server():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_server).start()
    main()