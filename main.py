#!/usr/bin/env python3
"""
X (Twitter) Worldwide Trends Telegram Bot
Runs daily at 12:00 and 00:00, sends top 10 worldwide trending topics to Telegram.

Usage:
  python main.py          # Start scheduler (runs at 12:00 and 00:00 daily)
  python main.py --once   # Run immediately once (for testing)
"""
import sys
import time
import logging

import schedule
from dotenv import load_dotenv

from scraper import get_worldwide_trends
from telegram_notifier import send_notification

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def job():
    log.info("Fetching worldwide X trends...")
    try:
        trends = get_worldwide_trends(limit=10)
        send_notification(trends)
        log.info("Telegram notification sent (%d trends)", len(trends))
    except Exception as exc:
        log.error("Job failed: %s", exc)


def main():
    if "--once" in sys.argv:
        job()
        return

    log.info("Scheduler started — will run at 12:00 and 00:00 every day")
    schedule.every().day.at("12:00").do(job)
    schedule.every().day.at("00:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
