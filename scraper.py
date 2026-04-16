import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

TRENDS_URL = "https://trends24.in/worldwide/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_worldwide_trends(limit=10):
    resp = requests.get(TRENDS_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # First .trend-card contains the most recent hour's trends
    card = soup.find("div", class_="trend-card")
    if not card:
        raise RuntimeError("Trend card not found on trends24.in — site structure may have changed")

    trends = []
    for item in card.select("ol li")[:limit]:
        link_tag = item.find("a")
        if not link_tag:
            continue
        topic = link_tag.get_text(strip=True)

        # Tweet count is typically in the last span of each list item
        spans = item.find_all("span")
        tweet_count = spans[-1].get_text(strip=True) if spans else None

        trends.append({
            "rank": len(trends) + 1,
            "topic": topic,
            "tweet_count": tweet_count,
            "url": f"https://x.com/search?q={quote(topic)}&src=trend_click",
        })

    if not trends:
        raise RuntimeError("No trends extracted — scraping may have failed")

    return trends
