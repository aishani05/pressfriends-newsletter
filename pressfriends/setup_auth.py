"""
Run this script once to authorize Gmail access.
It opens a browser window for you to log in and grant permission.
After completing auth, token.json is saved and send_newsletter.py
will use it automatically on every future run.

Usage:
    python setup_auth.py
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
BASE_DIR = Path(__file__).parent


def main():
    creds_path = BASE_DIR / "credentials.json"
    token_path = BASE_DIR / "token.json"

    if not creds_path.exists():
        print("ERROR: credentials.json not found.")
        print("Download it from Google Cloud Console → APIs & Services → Credentials.")
        print(f"Place it at: {creds_path}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w") as f:
        f.write(creds.to_json())

    print(f"Auth complete. Token saved to {token_path}")
    print("You can now run send_newsletter.py")


if __name__ == "__main__":
    main()
