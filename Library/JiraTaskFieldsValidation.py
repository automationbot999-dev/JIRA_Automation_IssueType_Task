import os
import json
from robot.api.deco import keyword, library
from playwright.sync_api import sync_playwright, expect
from robot.api import logger
import re

@library
class JiraTaskFieldsValidation:
    @keyword("Run Jira UI Flow With Fields")
    def run_jira_ui_flow_with_fields(self, issue_key):
        assignee_name = "JiraDemoUser"
        issue_priority = "High"
        label = "APIUITest"
        duedate = "2025-12-10"
        comment_text = "This is a test comment from UI."

        cookie_path = os.path.join(os.path.dirname(__file__), "jira_cookies.json")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError("jira_cookies.json not found in Library folder")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context()

            with open(cookie_path, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)

            page = context.new_page()
            page.set_default_timeout(20000)
            print("Navigating to Jira instance...")
            page.goto("https://automationbot999.atlassian.net", wait_until="domcontentloaded", timeout=60000)

            print("Opening project...")
            page.wait_for_selector("text=JiraAutomationDemo", timeout=30000)
            project_link = page.locator("a[href*='/browse/DEMO']").first
            project_link.scroll_into_view_if_needed()
            project_link.click(force=True)
            print("Project opened.")

            print(f"Opening issue: {issue_key}")
            page.wait_for_selector(f"text={issue_key}", timeout=30000)

            with page.expect_popup() as page1_info:
                page.get_by_text(issue_key).click()
            page1 = page1_info.value

            # Assign to user
            print("Assigning issue...")
            page1.wait_for_timeout(15000)
            assign_to_me = page1.get_by_test_id("issue-field-assignee-assign-to-me.ui.assign-to-me.link")
            if assign_to_me.is_visible():
                assign_to_me.click(force=True)
                print("Assign to : JiraDemoUser")
            else:
                print("Assign to me button not visible.")
                page1.screenshot(path="assign_to_me_not_visible.png")

            # Set priority
            print("Setting priority...")
            page1.get_by_test_id("issue-field-priority-readview-full.ui.priority.wrapper").click()
            page1.get_by_text(issue_priority, exact=True).click()
            expect(page1.get_by_test_id("issue-field-priority-readview-full.ui.priority.wrapper")
                   .locator("span")).to_contain_text(issue_priority)
            print(f"Priority set to: {issue_priority}")

            # Set due date
            print("Setting due date...")
            page1.get_by_role("heading", name="Due date").click()
            page1.get_by_test_id("issue.issue-view-layout.issue-view-date-field.duedate").get_by_text("None").click()
            page1.get_by_test_id("issue-field-date-editview-full.ui.date.issue-field-date-picker--open-calendar-button").click()
            page1.get_by_test_id("issue-field-date-editview-full.ui.date.issue-field-date-picker--calendar--next-month").click()
            page1.get_by_role("button", name="10, Wednesday December").click()
            print(f"Due date set to: {duedate}")

            # Set label
            print("Setting label...")
            page1.get_by_test_id("issue.views.issue-base.context.labels") \
                .get_by_test_id("issue-field-inline-edit-read-view-container.ui.container").click()

            label_input = page1.get_by_role("combobox", name="Labels")
            label_input.fill(label)
            page1.keyboard.press("Enter")
            page1.wait_for_timeout(1000)

            # Click outside to commit the label
            page1.get_by_test_id("issue.views.issue-base.foundation.summary.heading").click()
            page1.wait_for_timeout(1000)

            # Confirm label is visible
            label_container = page1.get_by_test_id("issue.views.issue-base.context.labels")
            expect(label_container).to_contain_text(label)
            print(f"Label set to: {label}")

            # Add comment
            # Ensure comment panel is visible
            page.get_by_test_id("issue-activity-feed.ui.buttons.Comments").click()

            # Scroll the comment section into view
            comment_placeholder = page.get_by_test_id("canned-comments.common.ui.comment-text-area-placeholder.textarea")
            comment_placeholder.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)  # give time for sticky header to move

            # Sometimes a floating toolbar still overlaps; use JS click to bypass it
            page.evaluate("el => el.click()", comment_placeholder.element_handle())

            # Wait for real editor to appear
            editor = page.locator('div[role="textbox"]')
            editor.wait_for(state="visible", timeout=10000)

            # Fill comment text
            editor.fill(comment_text)

            # Save and verify
            page.get_by_test_id("comment-save-button").click()
            expect(page.get_by_text(comment_text)).to_be_visible(timeout=5000)

            print(f"Comment set to: {comment_text}")


            logger.console(f"UI Updates Complete:\nAssignee: {assignee_name}\nPriority: {issue_priority}\nDue Date: {duedate}\nLabel: {label}\nComment: {comment_text}")

            context.close()
            browser.close()

            return assignee_name, issue_priority, duedate, label,comment_text
