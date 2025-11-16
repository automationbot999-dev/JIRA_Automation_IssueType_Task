
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Go directly to your Jira site
    page.goto("https://automationbot999.atlassian.net")

    input("Press Enter after you're fully logged in and see your Jira dashboard...")

    # Save cookies from the Jira domain
    cookies = context.cookies()
    with open("jira_cookies.json", "w") as f:
        json.dump(cookies, f)

    print("Jira session cookies saved.")
