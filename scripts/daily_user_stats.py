"""Daily "users today" report delivered to a Telegram channel.

Counts distinct users who were active today (local day in STATS_TIMEZONE):
logins/registrations from the audit log plus learning activity (practice,
games, quiz attempts, XP, exams, daily usage counters), so users who stay
signed in via a long-lived session cookie are still counted.

Configuration (environment):
  TELEGRAM_BOT_TOKEN   bot token from @BotFather (required to send)
  TELEGRAM_CHAT_ID     channel id such as -1001234567890 or @channelname (required to send)
  STATS_TIMEZONE       IANA timezone of "today" and of the send time (default Europe/Moscow)
  STATS_SEND_TIME      HH:MM local send time for --loop (default 18:00)

Usage:
  python scripts/daily_user_stats.py --dry-run   # print the message, send nothing
  python scripts/daily_user_stats.py             # send now, once
  python scripts/daily_user_stats.py --loop      # send every day at STATS_SEND_TIME
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
import urllib.error
import sys
import urllib.request
from datetime import datetime, time as dtime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, union

# Python puts /app/scripts at sys.path[0] rather than the repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (
    AuditLog,
    ExamResult,
    GameSession,
    PilotDailyUsage,
    PracticeResult,
    QuestionAttempt,
    SessionLocal,
    User,
    XPEvent,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mgc.daily_stats")


def _timezone() -> ZoneInfo:
    return ZoneInfo(os.getenv("STATS_TIMEZONE", "Europe/Moscow").strip() or "Europe/Moscow")


def _send_time() -> dtime:
    raw = os.getenv("STATS_SEND_TIME", "18:00").strip() or "18:00"
    hour, minute = raw.split(":", 1)
    return dtime(int(hour), int(minute))


def collect(db, tz: ZoneInfo, now: datetime | None = None) -> dict:
    now_local = (now or datetime.now(timezone.utc)).astimezone(tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start = start_local.astimezone(timezone.utc)
    day_key = start_local.date().isoformat()

    def since(model, column, user_column):
        return select(user_column.label("uid")).where(column >= start, user_column.is_not(None))

    logins = select(AuditLog.actor_user_id.label("uid")).where(
        AuditLog.event_type.in_(("auth.login", "auth.register")),
        AuditLog.created_at >= start,
        AuditLog.actor_user_id.is_not(None),
    )
    activity = [
        logins,
        since(PracticeResult, PracticeResult.created_at, PracticeResult.user_id),
        since(GameSession, GameSession.created_at, GameSession.user_id),
        since(QuestionAttempt, QuestionAttempt.created_at, QuestionAttempt.user_id),
        since(XPEvent, XPEvent.created_at, XPEvent.user_id),
        since(ExamResult, ExamResult.created_at, ExamResult.user_id),
        select(PilotDailyUsage.user_id.label("uid")).where(PilotDailyUsage.day_key == day_key),
    ]
    active_ids = union(*activity).subquery()
    active = int(db.scalar(select(func.count()).select_from(active_ids)) or 0)
    login_users = int(db.scalar(select(func.count(func.distinct(logins.subquery().c.uid)))) or 0)
    new_users = int(db.scalar(select(func.count()).select_from(User).where(User.created_at >= start)) or 0)
    total_users = int(db.scalar(select(func.count()).select_from(User)) or 0)
    return {
        "date": day_key,
        "time": now_local.strftime("%H:%M"),
        "active": active,
        "logins": login_users,
        "new": new_users,
        "total": total_users,
    }


def format_message(stats: dict) -> str:
    return (
        f"MGC Language Lab — {stats['date']}, {stats['time']}\n"
        f"Пользователей сегодня: {stats['active']}\n"
        f"  • входов в систему: {stats['logins']}\n"
        f"  • новых регистраций: {stats['new']}\n"
        f"Всего пользователей: {stats['total']}"
    )


def send_telegram(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
    body = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never log the URL: it contains the bot token.
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"Telegram API HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Telegram API unreachable: {exc.reason}") from None
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {str(payload)[:300]}")


def run_once(dry_run: bool = False) -> dict:
    with SessionLocal() as db:
        stats = collect(db, _timezone())
    message = format_message(stats)
    if dry_run:
        print(message)
    else:
        send_telegram(message)
        logger.info(json.dumps({"event": "daily_user_stats_sent", **stats}, ensure_ascii=False))
    return stats


def seconds_until_next_send(now: datetime, tz: ZoneInfo, at: dtime) -> float:
    local = now.astimezone(tz)
    target = local.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    if target <= local:
        target = (target + timedelta(days=1)).replace(hour=at.hour, minute=at.minute)
    return max(1.0, (target - local).total_seconds())


def main() -> int:
    parser = argparse.ArgumentParser(description="MGC daily users-today Telegram report")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--loop", action="store_true", help="send every day at STATS_SEND_TIME")
    mode.add_argument("--dry-run", action="store_true", help="print the message without sending")
    args = parser.parse_args()
    if not args.loop:
        run_once(args.dry_run)
        return 0
    tz, at = _timezone(), _send_time()
    logger.info(json.dumps({"event": "daily_user_stats_loop", "timezone": str(tz), "send_time": at.strftime("%H:%M")}))
    while True:
        time.sleep(seconds_until_next_send(datetime.now(timezone.utc), tz, at))
        try:
            run_once()
        except Exception as exc:
            logger.error(json.dumps({"event": "daily_user_stats_failed", "error": str(exc)}, ensure_ascii=False))
            time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
