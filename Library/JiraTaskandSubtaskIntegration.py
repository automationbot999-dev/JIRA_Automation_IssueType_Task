import os
import json
from robot.api.deco import keyword, library
from playwright.sync_api import sync_playwright, expect
from robot.api import logger

@library
class JiraTaskandSubtaskIntegration:
    @keyword("Run Jira UI Flow")
    def run_jira_ui_flow(self, issue_key):
        """
        Runs an end-to-end Jira UI validation and update flow:

        - Opens Jira using existing session cookies
        - Validates the issue panel
        - Creates a subtask and extracts its ID
        """

        subtask_summary = f"Subtask for {issue_key}"

        # Load cookies
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
            page.set_default_timeout(20000)
            print(" Navigating to Jira instance...")
            page.goto("https://automationbot999.atlassian.net", wait_until="domcontentloaded", timeout=60000)

            # Navigate to project
            print(" Waiting for project link...")
            page.wait_for_selector("text=JiraAutomationDemo", timeout=30000)
            project_link = page.locator("a[href*='/browse/DEMO']").first
            project_link.scroll_into_view_if_needed()
            project_link.click(force=True)
            print(" Project opened.")

            # Validate issue, summary and status
            print(" Validating issue panel for:", issue_key)
            breadcrumb = page.get_by_test_id("issue.views.issue-base.foundation.breadcrumbs.current-issue.item").locator("span")
            breadcrumb.wait_for(state="visible", timeout=15000)

            summary_heading = page.get_by_test_id("issue.views.issue-base.foundation.summary.heading")
            summary_heading.wait_for(state="visible", timeout=15000)

            actual_summary = summary_heading.inner_text().strip()
            expect(breadcrumb).to_contain_text(issue_key)
            expect(summary_heading).to_contain_text("Automated Test Issue")
            print(f"Issue {issue_key} is visible with summary '{actual_summary}'")


            #verify status
            status_element = page.locator("//span[normalize-space(text())='In Progress']")
            status_element.wait_for(state="visible", timeout=10000)
            status_text = status_element.inner_text()
            print(f" Status on UI: {status_text}")

            logger.console(f"UI : Issue {issue_key} is visible with summary '{actual_summary}'\nStatus on UI: {status_text}")

            # Create a subtask
            print("Creating subtask inline...")

            add_button = page.locator(
                "//div[@data-testid='issue-view-base.content.add-work-items.child-items-prompt.container']//button[@type='button']")
            add_button.wait_for(state="visible", timeout=10000)
            add_button.scroll_into_view_if_needed()
            add_button.click()
            page.wait_for_timeout(1000)

            subtask_input = page.locator("//input[@id='childIssuesPanel']")
            subtask_input.wait_for(state="visible", timeout=10000)
            subtask_input.fill(subtask_summary)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)

            # Confirm subtask creation
            page.wait_for_selector(f"text={subtask_summary}", timeout=15000)
            print(f" Subtask with name :'{subtask_summary}' created successfully.")
            logger.console(f"Subtask with name :'{subtask_summary}' created successfully in UI")

            # Locate subtask summary link using XPath and extract ID from href
            subtask_summary_xpath = f"//a[normalize-space()='{subtask_summary}']"
            subtask_summary_element = page.locator(subtask_summary_xpath)
            subtask_summary_element.wait_for(state="visible", timeout=15000)

            subtask_href = subtask_summary_element.get_attribute("href")
            subtask_id = subtask_href.split("/")[-1] if subtask_href else "UNKNOWN"

            print(f"Subtask created with ID: {subtask_id}")
            logger.console(f"Subtask ID extracted from UI: {subtask_id}")

            # Close modal if visible
            try:
                close_button = page.get_by_test_id("issue-view-foundation.modal-close-button")
                if close_button.is_visible():
                    close_button.click()
                    print(" Closed modal after subtask creation.")
            except:
                pass

            print(" Jira UI flow completed successfully.")
            #page.screenshot(path=f"jira_ui_flow_success_{issue_key}.png")

            context.close()
            browser.close()


