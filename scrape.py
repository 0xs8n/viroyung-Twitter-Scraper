import asyncio
from datetime import datetime, timedelta
from twscrape import API
from twscrape.logger import set_log_level
import requests
import json
import re
import os
import aiohttp
from urllib.parse import urlparse

# ============================================================================
# CONFIGURATION - REPLACE THESE VALUES WITH YOUR OWN
# ============================================================================

# Twitter/X Account Credentials
# You can add multiple accounts for better rate limits
X_ACCOUNTS = [
    {
        "username": "YOUR_TWITTER_USERNAME",
        "password": "YOUR_TWITTER_PASSWORD",
        "email": "YOUR_EMAIL@example.com",
        "email_password": "YOUR_EMAIL_PASSWORD",
        # Optional: Add cookies for already logged-in accounts
        # "cookies": '{"ct0": "your_ct0_token", "auth_token": "your_auth_token"}'
    },
    # Add more accounts if needed:
    # {
    #     "username": "another_account",
    #     "password": "another_password",
    #     "email": "another@example.com",
    #     "email_password": "email_password"
    # }
]

# Telegram Bot Configuration
# Get your bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
# Get your chat/channel ID (use @userinfobot or @getidsbot)
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

# ============================================================================
# SCRAPING SETTINGS - CUSTOMIZE THESE AS NEEDED
# ============================================================================

# Maximum age of tweets to scrape (in days)
MAX_AGE_DAYS = 1

# Minimum number of likes for a tweet to be considered viral
MIN_LIKES = 5000

# Tweet type filtering options:
# - "media_only": Only tweets with images/videos/GIFs
# - "text_only": Only text tweets (no media)
# - "all": All tweets (both media and text)
TWEET_TYPES = "media_only"

# How often to check for new tweets (in minutes)
CHECK_INTERVAL_MINUTES = 10

# Enable continuous monitoring (True) or run once (False)
CONTINUOUS_MONITORING = True

# File to track already-sent tweets (prevents duplicates)
SENT_TWEETS_FILE = "sent_tweets.txt"

# ============================================================================
# HELPER FUNCTIONS - NO NEED TO MODIFY BELOW THIS LINE
# ============================================================================

async def validate_media_url(url: str) -> bool:
    """Check if media URL is accessible"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=10) as response:
                return response.status == 200
    except Exception as e:
        print(f"Media validation failed for {url}: {e}")
        return False

async def send_telegram_photo(chat_id: str, photo_url: str, caption: str, bot_token: str):
    """Send photo to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "MarkdownV2"
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get("ok"):
            print(f"ERROR: Telegram sendPhoto failed: {response_json.get('description', 'No description')}")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Failed to send photo: {e}")
        return False

async def send_telegram_video(chat_id: str, video_url: str, caption: str, bot_token: str):
    """Send video to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    payload = {
        "chat_id": chat_id,
        "video": video_url,
        "caption": caption,
        "parse_mode": "MarkdownV2"
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get("ok"):
            print(f"ERROR: Telegram sendVideo failed: {response_json.get('description', 'No description')}")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Failed to send video: {e}")
        return False

async def send_telegram_message_with_media(chat_id: str, message: str, bot_token: str, media_items=None):
    """Send message with media, fallback to text if media fails"""
    if not media_items:
        return await send_telegram_message(chat_id, message, bot_token)
    
    # Try sending each media item
    for media_item in media_items:
        media_type = getattr(media_item, 'type', 'unknown').lower()
        media_url = getattr(media_item, 'url', None)
        
        if not media_url:
            continue
            
        print(f"Validating media URL: {media_url}")
        if not await validate_media_url(media_url):
            print(f"Media URL not accessible, skipping: {media_url}")
            continue
        
        # Send based on type
        if media_type in ['photo', 'image']:
            print(f"Sending as photo...")
            success = await send_telegram_photo(chat_id, media_url, message, bot_token)
            if success:
                return True
        elif media_type in ['video', 'animated_gif']:
            print(f"Sending as video...")
            success = await send_telegram_video(chat_id, media_url, message, bot_token)
            if success:
                return True
    
    # Fallback to text with media links
    print("Media failed, sending as text with links...")
    media_links = []
    for media_item in media_items:
        media_type = getattr(media_item, 'type', 'unknown')
        media_url = getattr(media_item, 'url', None)
        if media_url:
            media_link = create_safe_url_link(media_url, f"{media_type}")
            media_links.append(f"  \\- {media_link}")
    
    if media_links:
        message += "\n\n*Media*:\n" + "\n".join(media_links)
    
    return await send_telegram_message(chat_id, message, bot_token)

async def send_telegram_message(chat_id: str, message: str, bot_token: str):
    """Send text message to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get("ok"):
            print(f"ERROR: Telegram API error: {response_json.get('description', 'No description')}. Response: {response.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to send message: {e}. Response text: {getattr(e.response, 'text', 'No response text')}")
        return False

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2"""
    if not text:
        return ""
    
    text = str(text)
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def create_safe_url_link(url: str, display_text: str = None) -> str:
    """Create safe MarkdownV2 formatted link"""
    if not url:
        return ""
    
    if not display_text:
        display_text = "Link"
    
    safe_display_text = escape_markdown_v2(display_text)
    return f"[{safe_display_text}]({url})"

def load_sent_tweets() -> set:
    """Load already sent tweet IDs from file"""
    sent_tweets = set()
    if os.path.exists(SENT_TWEETS_FILE):
        try:
            with open(SENT_TWEETS_FILE, 'r') as f:
                for line in f:
                    tweet_id = line.strip()
                    if tweet_id:
                        sent_tweets.add(tweet_id)
            print(f"Loaded {len(sent_tweets)} previously sent tweet IDs.")
        except Exception as e:
            print(f"Error reading sent tweets file: {e}")
    else:
        print("No previous sent tweets file found. Starting fresh.")
    return sent_tweets

def save_sent_tweet(tweet_id: str):
    """Save tweet ID to file"""
    try:
        with open(SENT_TWEETS_FILE, 'a') as f:
            f.write(f"{tweet_id}\n")
    except Exception as e:
        print(f"Error saving tweet ID: {e}")

def cleanup_old_sent_tweets(sent_tweets: set, days_to_keep: int = 7):
    """Clean up old tweet IDs to prevent file bloat"""
    try:
        if len(sent_tweets) > 10000:
            sorted_tweets = sorted(sent_tweets, key=lambda x: int(x) if x.isdigit() else 0)
            sent_tweets_to_keep = set(sorted_tweets[-8000:])
            
            with open(SENT_TWEETS_FILE, 'w') as f:
                for tweet_id in sent_tweets_to_keep:
                    f.write(f"{tweet_id}\n")
            
            print(f"Cleaned up old tweet IDs. Kept {len(sent_tweets_to_keep)} recent ones.")
            return sent_tweets_to_keep
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    return sent_tweets

async def get_best_media_url(media_item):
    """Get best quality media URL from item"""
    possible_urls = []
    
    # Check different URL attributes
    for attr in ['url', 'media_url_https', 'media_url', 'preview_image_url']:
        url = getattr(media_item, attr, None)
        if url:
            possible_urls.append(url)
    
    # Return first working URL
    for url in possible_urls:
        if await validate_media_url(url):
            return url
    
    return None

async def scrape_viral_tweets():
    """Main function - initialize API and start monitoring"""
    set_log_level("INFO")
    api = API()
    sent_tweets = load_sent_tweets()
    sent_tweets = cleanup_old_sent_tweets(sent_tweets)

    print("--- Adding X Accounts ---")
    try:
        for acc in X_ACCOUNTS:
            if "cookies" in acc:
                await api.pool.add_account(
                    acc["username"],
                    acc["password"],
                    acc["email"],
                    acc["email_password"],
                    cookies=acc["cookies"]
                )
            else:
                await api.pool.add_account(
                    acc["username"],
                    acc["password"],
                    acc["email"],
                    acc["email_password"]
                )
        print(f"Successfully added {len(X_ACCOUNTS)} account(s).")
    except Exception as e:
        print(f"Error adding accounts: {e}")
        return

    print("--- Logging in Accounts ---")
    try:
        await api.pool.login_all()
        print("All accounts logged in.")
    except Exception as e:
        print(f"Error during login: {e}")

    cycle_count = 0
    total_tweets_sent = 0
    
    if CONTINUOUS_MONITORING:
        print(f"\nStarting continuous monitoring (checking every {CHECK_INTERVAL_MINUTES} minutes)")
        print("Press Ctrl+C to stop")
    
    try:
        while True:
            cycle_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n{'='*60}")
            print(f"MONITORING CYCLE #{cycle_count} - {current_time}")
            print(f"{'='*60}")
            
            new_tweets_found = await perform_scraping_cycle(api, sent_tweets)
            total_tweets_sent += new_tweets_found
            
            print(f"\nCycle #{cycle_count} Summary:")
            print(f"   New tweets sent: {new_tweets_found}")
            print(f"   Total tweets sent: {total_tweets_sent}")
            print(f"   Unique tweets tracked: {len(sent_tweets)}")
            
            if not CONTINUOUS_MONITORING:
                break
            
            print(f"\nWaiting {CHECK_INTERVAL_MINUTES} minutes before next check...")
            print(f"   Next check at: {(datetime.now() + timedelta(minutes=CHECK_INTERVAL_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')}")
            
            await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
            
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped by user")
        print(f"Final Statistics:")
        print(f"   Total cycles: {cycle_count}")
        print(f"   Total tweets sent: {total_tweets_sent}")
        print(f"   Unique tweets tracked: {len(sent_tweets)}")
    except Exception as e:
        print(f"\nError during monitoring: {e}")

async def perform_scraping_cycle(api, sent_tweets):
    """Perform one scraping cycle"""
    since_date = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    base_query = f"since:{since_date} min_faves:{MIN_LIKES}"
    
    if TWEET_TYPES == "media_only":
        query = f"{base_query} filter:media"
        query_description = "media tweets only (images, videos, GIFs)"
    elif TWEET_TYPES == "text_only":
        query = f"{base_query} -filter:media"
        query_description = "text-only tweets (no media)"
    else:
        query = base_query
        query_description = "all tweets (both media and text-only)"

    print(f"Searching for viral tweets ({query_description})")
    print(f"   Query: '{query}'")

    tweet_count = 0
    new_tweets_sent = 0
    duplicates_skipped = 0
    
    try:
        async for tweet in api.search(query, limit=50):
            tweet_count += 1
            tweet_id_str = str(tweet.id)
            
            if tweet_id_str in sent_tweets:
                duplicates_skipped += 1
                print(f"Skipping duplicate tweet ID: {tweet.id}")
                continue
            
            print(f"\nNew Tweet Found")
            print(f"   ID: {tweet.id}")
            print(f"   Author: @{tweet.user.username} ({tweet.user.displayname})")
            print(f"   Likes: {tweet.likeCount:,} | Retweets: {tweet.retweetCount:,} | Replies: {tweet.replyCount:,}")
            print(f"   Date: {tweet.date}")
            print(f"   Text: {tweet.rawContent[:100]}{'...' if len(tweet.rawContent) > 100 else ''}")

            # Prepare content
            tweet_content_display = ""
            if tweet.rawContent:
                if (tweet.rawContent.strip().startswith("http://") or 
                    tweet.rawContent.strip().startswith("https://")):
                    tweet_content_display = create_safe_url_link(tweet.rawContent.strip(), "Tweet Link")
                else:
                    tweet_content_display = escape_markdown_v2(tweet.rawContent)
            else:
                tweet_content_display = "*No text content*"

            tweet_url = f"https://twitter.com/{tweet.user.username}/status/{tweet.id}"
            tweet_link = create_safe_url_link(tweet_url, "View on X")

            telegram_message = f"""*VIRAL TWEET ALERT*

*Author*: @{escape_markdown_v2(tweet.user.username)} \\({escape_markdown_v2(tweet.user.displayname)}\\)
*Tweet ID*: `{escape_markdown_v2(str(tweet.id))}`
*Likes*: `{escape_markdown_v2(str(tweet.likeCount))}`
*Retweets*: `{escape_markdown_v2(str(tweet.retweetCount))}`
*Replies*: `{escape_markdown_v2(str(tweet.replyCount))}`
*Date*: `{escape_markdown_v2(str(tweet.date))}`

*Content*:
{tweet_content_display}

{tweet_link}"""

            # Handle media
            media_items = None
            if tweet.media:
                print("   Processing media...")
                media_items = tweet.media if isinstance(tweet.media, list) else [tweet.media]
                
                for i, media_item in enumerate(media_items):
                    media_type = getattr(media_item, 'type', 'unknown')
                    media_url = await get_best_media_url(media_item)
                    print(f"     Media {i+1}: Type={media_type}, URL={'Valid' if media_url else 'Invalid'}")

            # Send to Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                print(f"Sending tweet {tweet.id} to Telegram...")
                success = await send_telegram_message_with_media(
                    TELEGRAM_CHAT_ID, 
                    telegram_message, 
                    TELEGRAM_BOT_TOKEN,
                    media_items
                )
                
                if success:
                    print("Successfully sent to Telegram")
                    sent_tweets.add(tweet_id_str)
                    save_sent_tweet(tweet_id_str)
                    new_tweets_sent += 1
                else:
                    print("Failed to send to Telegram")
                
                print("Waiting 10 seconds before next tweet...")
                await asyncio.sleep(10)
            else:
                print("Telegram credentials not configured")

    except Exception as e:
        print(f"Error during scraping cycle: {e}")

    print(f"\nCycle Results:")
    print(f"   Total tweets found: {tweet_count}")
    print(f"   New tweets sent: {new_tweets_sent}")
    print(f"   Duplicates skipped: {duplicates_skipped}")
    
    return new_tweets_sent

if __name__ == "__main__":
    asyncio.run(scrape_viral_tweets())