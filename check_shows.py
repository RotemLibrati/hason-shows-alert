"""Check the Comedy Bar page for new Shahar Hason shows.

Every run: email right away if a new show appeared.
Once a day (first run after SUMMARY_HOUR, Israel time): email a summary of the last day's checks.
"""
import html
import json
import os
import re
import smtplib
import sys
import urllib.request
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

PAGE_URL = "https://comedybar.net/%D7%A9%D7%97%D7%A8-%D7%97%D7%A1%D7%95%D7%9F-%D7%94%D7%95%D7%A4%D7%A2%D7%95%D7%AA/"
HERE = Path(__file__).parent
# On a server, keep state outside the git checkout so `git pull` never conflicts.
STATE_DIR = Path(os.environ.get("STATE_DIR") or HERE)
STATE_FILE = STATE_DIR / "seen_shows.json"
LOG_FILE = STATE_DIR / "run_log.json"
TZ = ZoneInfo("Asia/Jerusalem")
SUMMARY_HOUR = 20

LINK_RE = re.compile(
    r'<a[^>]+href="(https://tickets\.comedybar\.net/[^"]*?[?&]id=(\d+)[^"]*)"[^>]*>(.*?)</a>',
    re.S,
)


def fetch_page():
    req = urllib.request.Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0 (show-alert)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_shows(page):
    """Return {show_id: {"url": ..., "details": [date, time, venue, ...]}}."""
    shows = {}
    for url, show_id, text in LINK_RE.findall(page):
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        text = " ".join(text.split())
        show = shows.setdefault(show_id, {"url": html.unescape(url), "details": []})
        if text and text not in show["details"]:
            show["details"].append(text)
    return shows


def send_email(subject, body):
    user = os.environ.get("GMAIL_USER", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    missing = [n for n, v in (("GMAIL_USER", user), ("GMAIL_APP_PASSWORD", password)) if not v]
    if missing:
        raise RuntimeError(f"missing GitHub secret(s): {', '.join(missing)}. "
                           "Check the names in Settings > Secrets and variables > Actions.")
    to = os.environ.get("ALERT_TO", "").strip() or user
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(f"Gmail rejected the login for {user}: {e}. "
                           "Make sure GMAIL_APP_PASSWORD is a 16-character App Password.") from e


def describe(show):
    return " | ".join(show["details"]) + "\n" + show["url"]


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def check_for_new_shows():
    """Run one check. Returns a log entry describing what happened."""
    shows = parse_shows(fetch_page())
    if not shows:
        raise RuntimeError("No shows found on the page - the site layout may have changed.")

    first_run = not STATE_FILE.exists()
    seen = load_json(STATE_FILE, {})
    new_ids = [i for i in shows if i not in seen]
    print(f"Found {len(shows)} shows, {len(new_ids)} new.")

    if first_run:
        print("First run: saving current shows without sending an email.")
        new_ids = []
    elif new_ids:
        body = "נפתחו הופעות חדשות של שחר חסון:\n\n"
        body += "\n\n".join(describe(shows[i]) for i in new_ids)
        body += f"\n\nכל ההופעות: {PAGE_URL}\n"
        send_email(f"שחר חסון: {len(new_ids)} הופעות חדשות!", body)
        print("Alert email sent.")

    # Saved only after the alert went out, so a failed email is retried next run.
    # Old shows are kept, so a show that disappears and comes back is not re-alerted.
    seen.update(shows)
    save_json(STATE_FILE, seen)
    return {"ok": True, "shows": len(shows),
            "new": [" | ".join(shows[i]["details"]) for i in new_ids]}


def build_summary(checks, now):
    ok = [c for c in checks if c["ok"]]
    failed = [c for c in checks if not c["ok"]]
    new = [n for c in ok for n in c["new"]]

    lines = [f"סיכום בדיקות הופעות שחר חסון ({now:%d.%m.%Y})", ""]
    lines.append(f"בדיקות מאז הסיכום הקודם: {len(checks)} (הצליחו: {len(ok)}, נכשלו: {len(failed)})")
    if checks:
        lines.append(f"בדיקה ראשונה: {checks[0]['time'][:16].replace('T', ' ')}")
        lines.append(f"בדיקה אחרונה: {checks[-1]['time'][:16].replace('T', ' ')}")
    if ok:
        lines.append(f"הופעות באתר כרגע: {ok[-1]['shows']}")
    lines.append("")

    if new:
        lines.append(f"נמצאו {len(new)} הופעות חדשות (נשלחה עליהן התראה בזמן אמת):")
        lines += [f"  • {n}" for n in new]
    else:
        lines.append("לא נמצאו הופעות חדשות.")

    if failed:
        lines += ["", "בדיקות שנכשלו:"]
        lines += [f"  • {c['time'][11:16]}: {c['error']}" for c in failed]

    lines += ["", f"עמוד ההופעות: {PAGE_URL}"]
    subject = f"שחר חסון - סיכום יומי: {len(new)} חדשות, {len(ok)}/{len(checks)} בדיקות תקינות"
    return subject, "\n".join(lines)


def summary_due(log, now):
    """True if a SUMMARY_HOUR deadline has passed since the last summary.

    GitHub often delays or skips scheduled runs, so the summary is sent by the
    first run after the deadline, even if that run happens after midnight.
    """
    deadline = now.replace(hour=SUMMARY_HOUR, minute=0, second=0, microsecond=0)
    if now < deadline:
        deadline -= timedelta(days=1)
    last = log.get("last_summary")
    if last is None:
        # Never sent: start counting from the first logged check.
        last = log["checks"][0]["time"]
    elif len(last) == 10:
        # Old format: a plain date means a summary was sent that evening.
        last += f"T{SUMMARY_HOUR:02d}:00:00+02:00"
    return datetime.fromisoformat(last) < deadline


def main():
    now = datetime.now(TZ)
    log = load_json(LOG_FILE, {"last_summary": None, "checks": []})

    error = None
    try:
        entry = check_for_new_shows()
    except Exception as e:
        error = e
        entry = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    entry["time"] = now.isoformat(timespec="seconds")
    log["checks"].append(entry)

    if summary_due(log, now):
        subject, body = build_summary(log["checks"], now)
        try:
            send_email(subject, body)
            print("Daily summary sent.")
            log["last_summary"] = now.isoformat(timespec="seconds")
            log["checks"] = []
        except Exception as e:
            # Keep the log so the summary is retried on the next run.
            error = error or e

    save_json(LOG_FILE, log)
    if error:
        sys.exit(f"ERROR: {error}")


if __name__ == "__main__":
    main()
