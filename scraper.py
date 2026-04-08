"""
news_scraper.py — A configurable web scraper for news/article websites.

Usage:
    python scraper.py --url <URL> [options]

Examples:
    python scraper.py --url https://news.ycombinator.com --pages 2 --output news.csv
    python scraper.py --url https://example-news.com \
        --article-selector "article" \
        --title-selector "h2 a" \
        --date-selector "time" \
        --summary-selector "p.excerpt" \
        --pages 3 --output articles.csv
"""

import argparse
import csv
import sys
import time
import urllib.parse
from dataclasses import dataclass, field, asdict

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Article:
    title: str
    url: str
    date: str
    summary: str


# ---------------------------------------------------------------------------
# Selector config
# ---------------------------------------------------------------------------

@dataclass
class Selectors:
    """CSS selectors used to locate article fields on the target site."""
    article: str = "article, .post, .news-item, .article, li.athing"
    title: str = "h1 a, h2 a, h3 a, .storylink, a.titlelink, a"
    date: str = "time, .date, .published, .post-date, .meta"
    summary: str = "p, .summary, .excerpt, .subtext, .description"
    next_page: str = 'a[rel="next"], .next a, a.morelink'


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

class NewsScraper:
    """Scrape news articles from a website and export them to CSV."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(
        self,
        base_url: str,
        selectors: Selectors | None = None,
        delay: float = 1.0,
    ) -> None:
        self.base_url = base_url
        self.sel = selectors or Selectors()
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    # ------------------------------------------------------------------
    # Network
    # ------------------------------------------------------------------

    def fetch_page(self, url: str) -> str | None:
        """Fetch a page and return HTML text, or None on failure."""
        for attempt in range(2):
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding
                return resp.text
            except requests.RequestException as exc:
                print(f"[警告] 第 {attempt + 1} 次請求失敗 {url}: {exc}", file=sys.stderr)
                if attempt == 0:
                    time.sleep(2)
        return None

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _first_text(self, tag, selectors: str) -> str:
        """Return stripped text from the first matching selector, or empty string."""
        for sel in selectors.split(","):
            el = tag.select_one(sel.strip())
            if el:
                # For <time> prefer the datetime attribute
                if el.name == "time" and el.get("datetime"):
                    return el["datetime"].strip()
                text = el.get_text(separator=" ", strip=True)
                if text:
                    return text
        return ""

    def _first_href(self, tag, selectors: str, page_url: str) -> str:
        """Return absolute href from the first matching selector, or empty string."""
        for sel in selectors.split(","):
            el = tag.select_one(sel.strip())
            if el:
                href = el.get("href", "")
                if href:
                    return urllib.parse.urljoin(page_url, href)
        return ""

    def parse_articles(self, html: str, page_url: str) -> list[Article]:
        """Extract a list of Article objects from raw HTML."""
        soup = BeautifulSoup(html, "lxml")
        articles: list[Article] = []

        for container in soup.select(self.sel.article):
            title = self._first_text(container, self.sel.title)
            url = self._first_href(container, self.sel.title, page_url)
            if not title and not url:
                continue  # skip empty containers

            # If title is still empty, use the text of the link
            if not title and url:
                title = url

            date = self._first_text(container, self.sel.date)
            summary = self._first_text(container, self.sel.summary)

            # Avoid duplicate title==summary
            if summary == title:
                summary = ""

            articles.append(Article(title=title, url=url, date=date, summary=summary))

        return articles

    def find_next_page(self, html: str, current_url: str) -> str | None:
        """Return the URL of the next page, or None if not found."""
        soup = BeautifulSoup(html, "lxml")
        el = soup.select_one(self.sel.next_page)
        if el and el.get("href"):
            return urllib.parse.urljoin(current_url, el["href"])
        return None

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------

    def scrape(self, pages: int = 1) -> list[Article]:
        """Scrape up to `pages` pages and return all collected articles."""
        all_articles: list[Article] = []
        current_url: str | None = self.base_url

        for page_num in range(1, pages + 1):
            if not current_url:
                break

            print(f"[{page_num}/{pages}] 爬取: {current_url}")
            html = self.fetch_page(current_url)
            if not html:
                print(f"  → 無法取得頁面，停止。", file=sys.stderr)
                break

            articles = self.parse_articles(html, current_url)
            print(f"  → 取得 {len(articles)} 篇文章")
            all_articles.extend(articles)

            if page_num < pages:
                next_url = self.find_next_page(html, current_url)
                if not next_url or next_url == current_url:
                    print("  → 找不到下一頁，停止。")
                    break
                current_url = next_url
                time.sleep(self.delay)

        return all_articles

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    @staticmethod
    def save_csv(articles: list[Article], output_path: str) -> None:
        """Write articles to a UTF-8 CSV file."""
        if not articles:
            print("沒有資料可以儲存。")
            return

        fields = ["title", "url", "date", "summary"]
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for article in articles:
                writer.writerow(asdict(article))

        print(f"已儲存 {len(articles)} 筆資料至 {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="新聞網站爬蟲 — 將文章標題、連結、日期、摘要輸出為 CSV",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--url", required=True, help="目標網站起始 URL")
    p.add_argument("--pages", type=int, default=1, help="最多爬取幾頁")
    p.add_argument("--output", default="articles.csv", help="輸出 CSV 檔案路徑")
    p.add_argument("--delay", type=float, default=1.0, help="每頁之間的等待秒數")

    sel = p.add_argument_group("CSS 選擇器 (選填，覆蓋預設值)")
    sel.add_argument("--article-selector", default=None, help="文章容器選擇器")
    sel.add_argument("--title-selector", default=None, help="標題 / 連結選擇器")
    sel.add_argument("--date-selector", default=None, help="日期選擇器")
    sel.add_argument("--summary-selector", default=None, help="摘要選擇器")
    sel.add_argument("--next-page-selector", default=None, help="下一頁選擇器")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    selectors = Selectors()
    if args.article_selector:
        selectors.article = args.article_selector
    if args.title_selector:
        selectors.title = args.title_selector
    if args.date_selector:
        selectors.date = args.date_selector
    if args.summary_selector:
        selectors.summary = args.summary_selector
    if args.next_page_selector:
        selectors.next_page = args.next_page_selector

    scraper = NewsScraper(
        base_url=args.url,
        selectors=selectors,
        delay=args.delay,
    )

    articles = scraper.scrape(pages=args.pages)
    scraper.save_csv(articles, args.output)


if __name__ == "__main__":
    main()
