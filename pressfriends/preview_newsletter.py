"""Renders the newsletter template to preview.html and opens it in the browser."""
import json, webbrowser
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
content = json.loads((BASE_DIR / "newsletter_content.json").read_text())
config  = json.loads((BASE_DIR / "config.json").read_text())

env = Environment(loader=FileSystemLoader(str(BASE_DIR)), autoescape=False)
html = env.get_template("template.html").render(
    recipient_name="Mary",
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

out = BASE_DIR / "preview.html"
out.write_text(html)
print(f"Saved to {out}")
webbrowser.open(f"file://{out}")
