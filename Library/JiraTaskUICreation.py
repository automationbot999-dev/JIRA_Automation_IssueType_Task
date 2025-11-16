import os
import json
import re
from robot.api.deco import keyword, library
from playwright.sync_api import sync_playwright, TimeoutError

@library
class JiraTaskUICreation:
    @keyword("Run Jira UI Flow To Create Issue")
    def run_jira_ui_flow_to_create_issue(self):
        summary = "Automated Test Issue_UI"

        cookie_path = os.path.join(os.path.dirname(__file__), "jira_cookies.json")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError("jira_cookies.json not found in Library folder")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=100)
            context = browser.new_context()

            with open(cookie_path, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)

            page = context.new_page()
            page.goto("https://automationbot999.atlassian.net/jira/for-you", wait_until="domcontentloaded", timeout=60000)

            # Navigate to project list view
            try:
                page.locator("div").filter(has_text=re.compile(r"^Quick links$")).click(timeout=10000)
                page.get_by_role("link", name=re.compile(r"JiraAutomationDemo Team-")).click(timeout=10000)
                page.get_by_role("link", name="List").click(timeout=10000)
            except TimeoutError:
                raise Exception("Navigation to project list view failed. Check if project is accessible.")

            # Trigger inline issue creation
            try:
                page.get_by_test_id("business-issue-create.ui.inline-create-trigger").click(timeout=10000)
            except TimeoutError:
                raise Exception("Inline create trigger not found. Check if you're in the correct view.")

            # Fill summary field using reliable placeholder selector
            try:
                summary_field = page.locator("textarea[placeholder='What needs to be done?']")
                summary_field.wait_for(state="visible", timeout=10000)
                summary_field.click()
                page.wait_for_timeout(300)
                summary_field.fill(summary)
            except TimeoutError:
                raise Exception("Summary field not found or not interactable.")

            # Click Create button
            page.get_by_test_id("business-list.ui.list-view.base-table.inline-create.inline-create-container") \
                .get_by_role("button", name="Create").click()

            # Wait for issue to appear and extract the latest issue key
            page.wait_for_timeout(3000)
            issue_rows = page.get_by_test_id(re.compile(r"business-list.ui.list-view.base-table.draggable-rows-container.row-wrapper-\d+"))
            latest_issue = issue_rows.nth(-1)
            issue_key = latest_issue.get_by_test_id("business-list.ui.list-view.key-cell.issue-key").inner_text()
            issue_summary = latest_issue.get_by_test_id("business-list.ui.list-view.summary-cell").inner_text()

            print(f"Issue created: {issue_key} with summary: {issue_summary}")

            context.close()
            browser.close()

            return issue_key

    @keyword("Open Issue In UI")
    def open_issue_in_ui(self, issue_key):
        cookie_path = os.path.join(os.path.dirname(__file__), "jira_cookies.json")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError("jira_cookies.json not found in Library folder")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=100)
            context = browser.new_context()

            with open(cookie_path, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)

            page = context.new_page()
            page.goto("https://automationbot999.atlassian.net/jira/for-you", wait_until="domcontentloaded", timeout=60000)

            # Navigate to project list view
            try:
                page.locator("div").filter(has_text=re.compile(r"^Quick links$")).click(timeout=10000)
                page.get_by_role("link", name=re.compile(r"JiraAutomationDemo Team-")).click(timeout=10000)
                page.get_by_role("link", name="List").click(timeout=10000)
            except TimeoutError:
                raise Exception("Navigation to project list view failed. Check if project is accessible.")

            # Try to locate the issue by key
            issue_locator = page.locator(f"text={issue_key}")
            if not issue_locator.is_visible():
                raise Exception(f"Issue not found in UI: {issue_key}")

            issue_locator.click()
            context.close()
            browser.close()
