import feedparser
import asyncio
import os
from datetime import datetime
from openai import OpenAI
from telegram import Bot

# Read from GitHub Secrets (environment variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
CHAT_IDS = os.environ.get("CHAT_IDS", "").split(",")

if not TELEGRAM_TOKEN or not DEEPSEEK_API_KEY or not CHAT_IDS or CHAT_IDS == [""]:
    raise Exception("Missing required environment variables: TELEGRAM_TOKEN, DEEPSEEK_API_KEY, CHAT_IDS")

# Your RSS feeds
RSS_FEEDS = [
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19206666",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6311",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=679471",
]

ARTICLES_PER_SOURCE = 3

telegram_bot = Bot(token=TELEGRAM_TOKEN)
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

def fetch_news_from_feed(feed_url):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:ARTICLES_PER_SOURCE]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if 'summary' in entry else "No summary available."
        })
    return articles

def summarize_article(article_text):
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "Summarize the news in 2-3 short Chinese sentences."},
                {"role": "user", "content": f"News: {article_text}"}
            ],
            max_tokens=5000,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Summarization error: {e}")
        return "⚠️ Could not generate summary."

async def send_telegram_message(message):
    for chat_id in CHAT_IDS:
        if not chat_id.strip():
            continue
        try:
            await telegram_bot.send_message(
                chat_id=chat_id.strip(),
                text=message,
                parse_mode="Markdown"
            )
            print(f"Sent to {chat_id}")
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
        await asyncio.sleep(0.5)

async def main():
    print(f"[{datetime.now()}] Starting...")
    for feed_url in RSS_FEEDS:
        if not feed_url:
            continue
        print(f"Processing: {feed_url}")
        articles = fetch_news_from_feed(feed_url)
        for article in articles:
            print(f"Summarizing: {article['title'][:40]}...")
            summary = summarize_article(article['summary'])
            message = f"*{article['title']}*\n\n{summary}\n\n[Read more]({article['link']})\n---"
            await send_telegram_message(message)
            await asyncio.sleep(1)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
