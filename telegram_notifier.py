import os
import requests
from datetime import datetime

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

RANK_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def format_message(trends):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "🌍 <b>X (Twitter) 全球熱門話題 TOP 10</b>",
        f"📅 {now}",
        "",
    ]
    for t in trends:
        emoji = RANK_EMOJIS[t["rank"] - 1] if t["rank"] <= 10 else f"{t['rank']}."
        count = f" <i>{t['tweet_count']}</i>" if t.get("tweet_count") else ""
        lines.append(f'{emoji} <a href="{t["url"]}">{t["topic"]}</a>{count}')
    lines += ["", "🔗 資料來源: trends24.in"]
    return "\n".join(lines)


def send_notification(trends):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = {
        "chat_id": chat_id,
        "text": format_message(trends),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(
        TELEGRAM_API.format(token=token),
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
