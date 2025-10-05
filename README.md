# Twitter Viral Tweet Scraper

Automatically monitors Twitter/X for viral tweets and posts them to your Telegram channel. Perfect for tracking trending content, memecoin narratives, or any viral Twitter activity.

## Features

- Monitors Twitter for viral tweets based on customizable criteria
- Automatically posts to Telegram with media support (photos, videos, GIFs)
- Prevents duplicate posts with built-in tracking
- Continuous monitoring with configurable intervals
- Filters by media type (media-only, text-only, or all)
- Handles multiple Twitter accounts for better rate limits

## Prerequisites

- Python 3.7+
- A Twitter/X account
- A Telegram bot token
- A Telegram channel or group

## Installation

1. Clone this repository:
```bash
git clone https://github.com/0xs8n/twitter-viral-scraper.git
cd twitter-viral-scraper
```

2. Install required dependencies:
```bash
pip install twscrape requests aiohttp
```

## Setup

### 1. Get Your Telegram Bot Token

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Save the bot token (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Add your bot to your channel/group as an administrator

### 2. Get Your Telegram Chat ID

**For Channels:**
1. Forward a message from your channel to [@userinfobot](https://t.me/userinfobot)
2. The bot will reply with the channel ID (starts with `-100`)

**For Groups:**
1. Add [@userinfobot](https://t.me/userinfobot) to your group
2. The bot will send the group ID

**Alternative method:**
1. Add your bot to the channel/group
2. Send a message to the channel/group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":` in the response

### 3. Configure the Script

Open `scraper.py` and edit the configuration section at the top:

```python
# Twitter/X Account Credentials
X_ACCOUNTS = [
    {
        "username": "YOUR_TWITTER_USERNAME",
        "password": "YOUR_TWITTER_PASSWORD",
        "email": "YOUR_EMAIL@example.com",
        "email_password": "YOUR_EMAIL_PASSWORD",
    },
]

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
```

### 4. Customize Settings (Optional)

Adjust these parameters based on your needs:

```python
# Minimum number of likes for a tweet to be considered viral
MIN_LIKES = 5000

# Maximum age of tweets to scrape (in days)
MAX_AGE_DAYS = 1

# Tweet type filtering:
# - "media_only": Only tweets with images/videos/GIFs
# - "text_only": Only text tweets (no media)
# - "all": All tweets
TWEET_TYPES = "media_only"

# How often to check for new tweets (in minutes)
CHECK_INTERVAL_MINUTES = 10

# Enable continuous monitoring (True) or run once (False)
CONTINUOUS_MONITORING = True
```

## Usage

Run the script:
```bash
python scraper.py
```

The script will:
1. Log in to your Twitter account(s)
2. Search for viral tweets matching your criteria
3. Post new tweets to your Telegram channel
4. Continue monitoring every X minutes (based on `CHECK_INTERVAL_MINUTES`)

To stop the script, press `Ctrl+C`.

### "Failed to send to Telegram"
- Verify your bot token is correct
- Ensure your bot is added to the channel/group as an administrator
- Check that the chat ID is correct (should start with `-` for channels/groups)

### No tweets found
- Lower the `MIN_LIKES` threshold
- Increase `MAX_AGE_DAYS`
- Change `TWEET_TYPES` to "all" to include more tweets
- Check that your Twitter account has API access

### Rate limiting issues
- Add multiple Twitter accounts to the `X_ACCOUNTS` list
- Increase `CHECK_INTERVAL_MINUTES`
- The script includes a 10-second delay between tweets

## Advanced Configuration

### Using Multiple Twitter Accounts

Add more accounts to improve rate limits:

```python
X_ACCOUNTS = [
    {
        "username": "account1",
        "password": "password1",
        "email": "email1@example.com",
        "email_password": "emailpass1",
    },
    {
        "username": "account2",
        "password": "password2",
        "email": "email2@example.com",
        "email_password": "emailpass2",
    },
]
```

### Using Cookies for Authentication

If you have an already logged-in Twitter session:

```python
X_ACCOUNTS = [
    {
        "username": "your_username",
        "password": "your_password",
        "email": "your_email@example.com",
        "email_password": "email_password",
        "cookies": '{"ct0": "your_ct0_token", "auth_token": "your_auth_token"}'
    },
]
```

## Use Cases

- **Memecoin Trading**: Track viral crypto narratives before they explode
- **Content Curation**: Aggregate trending content for your community
- **Market Research**: Monitor viral topics in your industry
- **News Monitoring**: Stay updated on breaking viral stories
- **Trend Analysis**: Track what's going viral in real-time

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is provided as-is for educational purposes. Please ensure you comply with Twitter's Terms of Service and API usage guidelines.

## Disclaimer

This tool is for educational and research purposes only. Users are responsible for complying with:
- Twitter/X Terms of Service
- Telegram Terms of Service
- Applicable data privacy laws
- Rate limiting and API usage policies

Use responsibly and at your own risk.

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review the [twscrape documentation](https://github.com/vladkens/twscrape)
3. Open an issue on GitHub with details about your problem

---

**Note**: This project uses the `twscrape` library for Twitter scraping. Make sure you're familiar with its limitations and requirements.
