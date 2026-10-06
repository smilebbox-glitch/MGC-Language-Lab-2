from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_compose_overlay_contract() -> None:
    text = (ROOT / "docker-compose.telegram-stats.yml").read_text(encoding="utf-8")
    assert "daily_user_stats.py\", \"--loop\"" in text
    assert "TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:?" in text
    assert "networks: [backend, egress]" in text
    assert "ports:" not in text
    example = (ROOT / ".env.telegram-stats.example").read_text(encoding="utf-8")
    assert "CHANGE_ME_BOT_TOKEN" in example


def test_dry_run_counts_distinct_active_users(tmp_path: Path) -> None:
    db = tmp_path / "stats.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}", "AUTO_CREATE_SCHEMA": "true", "PYTHONPATH": str(ROOT)}
    seed = (
        "from datetime import datetime, timedelta, timezone\n"
        "from app import SessionLocal, User, AuditLog, PilotDailyUsage\n"
        "import datetime as dt\n"
        "with SessionLocal() as db:\n"
        "    us=[User(username=f'u{i}',display_name='U',password_hash='x') for i in range(3)]\n"
        "    db.add_all(us); db.flush()\n"
        "    db.add(AuditLog(event_type='auth.login',actor_user_id=us[0].id))\n"
        "    db.add(AuditLog(event_type='auth.login',actor_user_id=us[1].id,created_at=datetime.now(timezone.utc)-timedelta(days=3)))\n"
        "    db.add(PilotDailyUsage(user_id=us[0].id,day_key=dt.date.today().isoformat()))\n"
        "    db.commit()\n"
    )
    subprocess.run([sys.executable, "-c", seed], check=True, cwd=ROOT, env=env)
    out = subprocess.run(
        [sys.executable, "scripts/daily_user_stats.py", "--dry-run"],
        check=True, cwd=ROOT, env={**env, "STATS_TIMEZONE": "UTC"}, capture_output=True, text=True,
    ).stdout
    assert "Пользователей сегодня: 1" in out
    assert "Всего пользователей: 3" in out


def test_send_requires_credentials() -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("TELEGRAM_")}
    env.update({"DATABASE_URL": "sqlite:////tmp/mgc_stats_creds.db", "AUTO_CREATE_SCHEMA": "true", "PYTHONPATH": str(ROOT)})
    run = subprocess.run([sys.executable, "scripts/daily_user_stats.py"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert run.returncode != 0
    assert "TELEGRAM_BOT_TOKEN" in run.stderr
