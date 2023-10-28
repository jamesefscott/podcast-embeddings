import feedparser
import time
import re

def get_rss_episodes(feed_url):

    def get_mp3_url(entry):
        mp3_links = [
            link['href']
            for link in entry["links"]
            if link["type"] == "audio/mpeg" and re.search(r'\.mp3(\?|$)', link["href"])
        ]
        if mp3_links:
            return mp3_links[0]
        
        return ''

    rss_parsed = feedparser.parse(feed_url)

    all_rss_episodes = [
        {
            "title": entry["title"],
            "published": entry["published_parsed"],
            "date_str": time.strftime("%Y-%m-%d", entry["published_parsed"]),
            "mp3_url": get_mp3_url(entry)
        }
        for entry in rss_parsed.entries
    ]

    return all_rss_episodes