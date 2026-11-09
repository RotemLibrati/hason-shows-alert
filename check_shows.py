"""Check the Comedy Bar page for new Shahar Hason shows and email when one appears."""
import html
import json
import os
import re
import smtplib
import sys
import urllib.request
from email.mime.text import MIMEText
from pathlib import Path

PAGE_URL = "https://comedybar.net/%D7%A9%D7%97%D7%A8-%D7%97%D7%A1%D7%95%D7%9F-%D7%94%D7%95%D7%A4%D7%A2%D7%95%D7%AA/"
STATE_FILE = Path(__file__).with_name("seen_shows.json")

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
        sys.exit(f"ERROR: missing GitHub secret(s): {', '.join(missing)}. "
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
        sys.exit(f"ERROR: Gmail rejected the login for {user}: {e}. "
                 "Make sure GMAIL_APP_PASSWORD is a 16-character App Password, not your normal password.")


def describe(show):
    return " | ".join(show["details"]) + "\n" + show["url"]


def main():
    shows = parse_shows(fetch_page())
    if not shows:
        # Probably the site layout changed. Fail loudly so GitHub emails about the failed run.
        sys.exit("No shows found on the page - the site layout may have changed.")

    first_run = not STATE_FILE.exists()
    seen = {} if first_run else json.loads(STATE_FILE.read_text(encoding="utf-8"))
    new_ids = [i for i in shows if i not in seen]

    print(f"Found {len(shows)} shows, {len(new_ids)} new.")
    for i in new_ids:
        print("  NEW:", describe(shows[i]).replace("\n", "  "))

    if first_run:
        print("First run: saving current shows without sending an email.")
    elif new_ids:
        body = "נפתחו הופעות חדשות של שחר חסון:\n\n"
        body += "\n\n".join(describe(shows[i]) for i in new_ids)
        body += f"\n\nכל ההופעות: {html.unescape(PAGE_URL)}\n"
        send_email(f"שחר חסון: {len(new_ids)} הופעות חדשות!", body)
        print("Email sent.")

    # Keep shows we've seen before, so a show that disappears and comes back is not re-alerted.
    seen.update(shows)
    STATE_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
