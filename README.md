# PressFriends Newsletter Agent

An automated monthly email newsletter agent built for **PressFriends**, a student-run 501(c)(3) nonprofit. Sends personalized HTML newsletters to parents and donors via the Gmail API — fully automated on the 1st of every month.

## Features

- Personalized emails (each recipient gets their own first name in the greeting)
- Professional HTML template with hero photo and volunteer spotlight sections
- Dry-run and test modes so you can preview before sending
- Crash-safe: re-running never sends duplicates
- Per-month CSV send logs
- Mac launchd scheduler (runs even after the machine wakes from sleep)

## Project Structure

```
pressfriends/
├── send_newsletter.py       # Main agent — renders + sends all emails
├── setup_auth.py            # One-time Gmail OAuth setup
├── install_scheduler.sh     # Auto-installs the monthly Mac scheduler
├── template.html            # HTML email design
├── contacts.csv             # Contact list (first_name, last_name, email, role)
├── newsletter_content.json  # Monthly content — update this each month
├── preview_newsletter.py    # Renders preview.html and opens it in your browser
└── requirements.txt         # Python dependencies
requirements.txt             # Same dependencies (repo root for convenience)
```

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/aishani05/test.git
cd test
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get Gmail API credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable the **Gmail API** (APIs & Services → Enable APIs)
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
4. Download the JSON file and save it as `pressfriends/credentials.json`

### 3. Authorize Gmail

```bash
python pressfriends/setup_auth.py
```

A browser window opens — log in with the Gmail account you want to send from. This saves a `token.json` and only needs to be done once.

### 4. Configure the agent

Edit `pressfriends/config.json`:

```json
{
  "org_name": "PressFriends",
  "sender_name": "PressFriends Team",
  "sender_email": "your-gmail@gmail.com",
  "subject_template": "PressFriends Newsletter — {month_year}",
  "donation_link": "https://your-donation-link.com",
  "volunteer_link": "https://your-volunteer-link.com",
  "unsubscribe_email": "unsubscribe@yourdomain.com"
}
```

### 5. Add your contacts

Edit `pressfriends/contacts.csv` — one row per recipient:

```
first_name,last_name,email,role
Mary,Smith,mary.smith@gmail.com,parent
John,Doe,john.doe@gmail.com,donor
```

## Usage

**Preview the newsletter in your browser:**
```bash
python pressfriends/preview_newsletter.py
```

**Test send to a single address:**
```bash
python pressfriends/send_newsletter.py --test you@gmail.com
```

**Send to all contacts:**
```bash
python pressfriends/send_newsletter.py
```

**Dry run (renders all emails, sends nothing):**
```bash
python pressfriends/send_newsletter.py --dry-run
```

## Monthly Workflow

1. Open `pressfriends/newsletter_content.json` and update:
   - `month_year` — e.g. `"June 2026"`
   - `headline` — the main story headline
   - `body_paragraphs` — list of paragraph strings
   - `featured_story` — volunteer spotlight text
   - `hero_image_url` / `spotlight_image_url` — paste public photo URLs (e.g. from [Pexels](https://www.pexels.com))

2. Preview: `python pressfriends/preview_newsletter.py`

3. Test: `python pressfriends/send_newsletter.py --test you@gmail.com`

4. Send: `python pressfriends/send_newsletter.py`

## Automate Monthly Sends (Mac only)

Installs a launchd job that fires on the 1st of every month at 9:00am:

```bash
chmod +x pressfriends/install_scheduler.sh
./pressfriends/install_scheduler.sh
```

> **Note:** You still need to update `newsletter_content.json` before the 1st each month. The scheduler handles the send automatically once the content is ready.

## Notes

- `credentials.json` and `token.json` are gitignored — never commit them
- Send logs are saved to `pressfriends/logs/sent_YYYY-MM.csv` (also gitignored)
- Gmail free accounts can send up to 500 emails/day; Google Workspace up to 2,000
