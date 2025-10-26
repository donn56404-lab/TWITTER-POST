#!/usr/bin/env python3
"""
Twitter Automation Script (Daily 17 posts, supports multi-line posts inside "")
---------------------------------------------------------------------------
- Reads posts from post.txt where each post is wrapped in double quotes (")
- Each day:
    • Posts 8 normal tweets (with random images if available)
    • Posts 9 replies to influencers' latest tweets
- After posting 17:
    • Saves URLs to normal_posts.txt and influencer_posts.txt
    • Removes those 17 posts from post.txt
- Waits 24 hours before continuing
- Includes a dummy Flask web server (for hosting/keep-alive)
"""

import tweepy
import os
import time
import random
import re
from threading import Thread
from flask import Flask

# ====== CONFIG ======
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
ACCESS_SECRET = "YOUR_ACCESS_SECRET"

POST_FILE = "post.txt"
INFLUENCERS_FILE = "influencers.txt"
IMAGES_FOLDER = "images"
NORMAL_OUT = "normal_posts.txt"
INFLUENCER_OUT = "influencer_posts.txt"

POSTS_PER_DAY = 17
SLEEP_BETWEEN_POSTS = 60  # seconds between posts
WAIT_BETWEEN_DAYS = 24 * 3600  # 24 hours

# ====== SETUP ======
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# ====== HELPERS ======
def load_posts(path):
    """Read posts from file separated by quotes."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    posts = re.findall(r'"(.*?)"', content, re.DOTALL)
    posts = [p.strip() for p in posts if p.strip()]
    return posts

def save_remaining_posts(path, remaining_posts):
    """Rewrite remaining posts (still wrapped in quotes)."""
    with open(path, "w", encoding="utf-8") as f:
        for p in remaining_posts:
            f.write(f'"{p.strip()}"\n\n')

def load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def save_line(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def post_tweet(text, image_path=None):
    try:
        if image_path and os.path.exists(image_path):
            media = api.media_upload(image_path)
            tweet = api.update_status(status=text, media_ids=[media.media_id_string])
        else:
            tweet = api.update_status(status=text)
        url = f"https://x.com/{tweet.user.screen_name}/status/{tweet.id_str}"
        return url
    except Exception as e:
        print("❌ Error posting tweet:", e)
        return None

def get_latest_tweet_id(handle):
    try:
        tweets = api.user_timeline(screen_name=handle, count=1, exclude_replies=False, include_rts=False)
        if tweets:
            return tweets[0].id
    except Exception as e:
        print(f"⚠️ Failed to fetch tweet for {handle}: {e}")
    return None

def reply_to_tweet(tweet_id, text, image_path=None):
    try:
        if image_path and os.path.exists(image_path):
            media = api.media_upload(image_path)
            reply = api.update_status(status=text, in_reply_to_status_id=tweet_id,
                                      auto_populate_reply_metadata=True, media_ids=[media.media_id_string])
        else:
            reply = api.update_status(status=text, in_reply_to_status_id=tweet_id,
                                      auto_populate_reply_metadata=True)
        url = f"https://x.com/{reply.user.screen_name}/status/{reply.id_str}"
        return url
    except Exception as e:
        print("❌ Error replying:", e)
        return None

def pick_random_image():
    if not os.path.exists(IMAGES_FOLDER):
        return None
    imgs = [os.path.join(IMAGES_FOLDER, f) for f in os.listdir(IMAGES_FOLDER)
            if os.path.isfile(os.path.join(IMAGES_FOLDER, f))]
    if not imgs:
        return None
    return random.choice(imgs)

# ====== MAIN LOOP ======
def main():
    while True:
        posts = load_posts(POST_FILE)
        if not posts:
            print("✅ All posts completed!")
            break

        influencers = load_lines(INFLUENCERS_FILE)
        if not influencers:
            print("⚠️ influencers.txt is empty, skipping replies.")
            break

        daily_posts = posts[:POSTS_PER_DAY]
        remaining_posts = posts[POSTS_PER_DAY:]

        half = POSTS_PER_DAY // 2
        normal_posts = daily_posts[:half]
        influencer_posts = daily_posts[half:]

        print(f"🚀 Starting new day with {len(daily_posts)} posts...")

        # ---- Normal posts ----
        for text in normal_posts:
            img = pick_random_image()
            url = post_tweet(text, img)
            if url:
                print(f"✅ Posted normal tweet: {url}")
                save_line(NORMAL_OUT, url)
            time.sleep(SLEEP_BETWEEN_POSTS)

        # ---- Influencer replies ----
        for text in influencer_posts:
            handle = random.choice(influencers).lstrip("@").strip()
            tweet_id = get_latest_tweet_id(handle)
            if not tweet_id:
                print(f"⚠️ Could not get tweet for @{handle}, skipping.")
                continue
            img = pick_random_image()
            url = reply_to_tweet(tweet_id, text, img)
            if url:
                print(f"💬 Replied to @{handle}: {url}")
                save_line(INFLUENCER_OUT, url)
            time.sleep(SLEEP_BETWEEN_POSTS)

        # ---- Remove used posts ----
        save_remaining_posts(POST_FILE, remaining_posts)
        print(f"✅ Removed {POSTS_PER_DAY} posts from post.txt")

        print(f"🌙 Done for the day. Waiting 24 hours...")
        time.sleep(WAIT_BETWEEN_DAYS)

# ====== DUMMY WEB SERVER ======
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Twitter automation bot is running perfectly!"

def run_server():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    # Run Flask server in background
    Thread(target=run_server).start()

    # Start main logic
    main()