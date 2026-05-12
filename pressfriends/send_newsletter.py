"""
PressFriends Monthly Newsletter Agent
--------------------------------------
Reads contacts from contacts.csv, renders the HTML template with this
month's content from newsletter_content.json, and sends personalized
emails via Gmail API. Logs results to logs/sent_YYYY-MM.csv.

Usage:
    python send_newsletter.py              # send to all contacts
    python send_newsletter.py --dry-run   # preview without sending
    python send_newsletter.py --test me@example.com  # send only to one address
"""

import argparse
import base64
import csv
import json
import logging
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from jinja2 import Environment, FileSystemLoader

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
BASE_DIR = Path(__file__).parent
DELAY_BETWEEN_SENDS = 0.5  # seconds — stays well under Gmail's rate limits


def get_gmail_service():
    creds = None
    token_path = BASE_DIR / "token.json"
    creds_path = BASE_DIR / "credentials.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                logging.error("credentials.json not found. Run setup_auth.py first.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def load_contacts():
    with open(BASE_DIR / "contacts.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_content():
    with open(BASE_DIR / "newsletter_content.json", encoding="utf-8") as f:
        return json.load(f)


def load_config():
    with open(BASE_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def render_email(template_env, contact, content, config):
    template = template_env.get_template("template.html")
    return template.render(
        recipient_name=contact["first_name"],
        month_year=content["month_year"],
        hero_image_url=content.get("hero_image_url", ""),
        hero_image_alt=content.get("hero_image_alt", ""),
        headline=content["headline"],
        body_paragraphs=content["body_paragraphs"],
        featured_story=content.get("featured_story", ""),
        spotlight_image_url=content.get("spotlight_image_url", ""),
        spotlight_image_alt=content.get("spotlight_image_alt", ""),
        donation_link=config["donation_link"],
        volunteer_link=config["volunteer_link"],
        org_name=config["org_name"],
        unsubscribe_email=config["unsubscribe_email"],
    )


def build_mime_message(sender, recipient_email, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_one(service, message):
    return service.users().messages().send(userId="me", body=message).execute()


def main():
    parser = argparse.ArgumentParser(description="PressFriends newsletter sender")
    parser.add_argument("--dry-run", action="store_true", help="Render emails but do not send")
    parser.add_argument("--test", metavar="EMAIL", help="Send only to this address (for testing)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    config = load_config()
    content = load_content()
    contacts = load_contacts()

    if args.dry_run:
        logging.info("DRY RUN — emails will be rendered but not sent.")

    service = None
    if not args.dry_run:
        service = get_gmail_service()

    env = Environment(loader=FileSystemLoader(str(BASE_DIR)), autoescape=False)
    subject = config["subject_template"].format(month_year=content["month_year"])
    sender = f"{config['sender_name']} <{config['sender_email']}>"

    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"sent_{datetime.now().strftime('%Y-%m')}.csv"

    # Load emails already sent this month so re-runs never duplicate
    already_sent: set[str] = set()
    if log_file.exists() and not args.dry_run:
        with open(log_file, newline="", encoding="utf-8") as existing:
            for row in csv.DictReader(existing):
                if row.get("status") == "sent":
                    already_sent.add(row["email"].strip())
        if already_sent:
            logging.info(f"Resuming — skipping {len(already_sent)} already-sent addresses.")

    # In --test mode, send to a synthetic contact at the given address
    if args.test:
        test_match = next((c for c in contacts if c["email"].strip() == args.test), None)
        if test_match:
            contacts = [test_match]
        else:
            contacts = [{"first_name": "Test", "last_name": "User", "email": args.test, "role": "test"}]
            logging.info(f"Test address not in contacts.csv — using placeholder name 'Test User'.")

    sent_count = 0
    failed_count = 0
    skipped_count = 0

    log_mode = "a" if log_file.exists() and not args.dry_run else "w"
    write_header = log_mode == "w"

    with open(log_file, log_mode, newline="", encoding="utf-8") as lf:
        writer = csv.writer(lf)
        if write_header:
            writer.writerow(["timestamp", "email", "name", "role", "status", "message_id"])

        for contact in contacts:
            recipient_email = contact["email"].strip()

            if recipient_email in already_sent:
                skipped_count += 1
                logging.info(f"Skipping {recipient_email} — already sent this month.")
                continue

            name = f"{contact['first_name']} {contact['last_name']}"

            try:
                html_body = render_email(env, contact, content, config)

                if args.dry_run:
                    logging.info(f"[DRY RUN] Would send to {recipient_email} ({name})")
                    writer.writerow([datetime.now().isoformat(), recipient_email, name, contact["role"], "dry_run", ""])
                    sent_count += 1
                    continue

                mime_msg = build_mime_message(sender, recipient_email, subject, html_body)
                result = send_one(service, mime_msg)
                msg_id = result.get("id", "")
                writer.writerow([datetime.now().isoformat(), recipient_email, name, contact["role"], "sent", msg_id])
                sent_count += 1
                logging.info(f"Sent to {recipient_email} ({name})")
                time.sleep(DELAY_BETWEEN_SENDS)

            except HttpError as e:
                logging.error(f"Gmail API error for {recipient_email}: {e}")
                writer.writerow([datetime.now().isoformat(), recipient_email, name, contact["role"], "failed", str(e)])
                failed_count += 1

            except Exception as e:
                logging.error(f"Unexpected error for {recipient_email}: {e}")
                writer.writerow([datetime.now().isoformat(), recipient_email, name, contact["role"], "failed", str(e)])
                failed_count += 1

    status = "DRY RUN complete" if args.dry_run else "Send complete"
    logging.info(f"{status}: {sent_count} sent, {failed_count} failed, {skipped_count} skipped")
    logging.info(f"Log saved to {log_file}")


if __name__ == "__main__":
    main()
