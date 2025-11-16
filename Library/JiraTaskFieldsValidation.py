import os
import json
from robot.api.deco import keyword, library
from playwright.sync_api import sync_playwright, expect, TimeoutError
from robot.api import logger


@library
class JiraTaskFieldsValidation:

    @keyword("Run Jira UI Flow With Fields")
    def run_jira_ui_flow_with_fields(self, issue_key):
        assignee_name = "JiraDemoUser"
        issue_priority = "High"
        label = "APIUITest"
        comment_text = "This is a test comment from UI."

        # ================================ LOAD COOKIES ================================
        cookie_path = os.path.join(os.path.dirname(__file__), "jira_cookies.json")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError("jira_cookies.json not found in Library folder")

        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        # ================================ START PLAYWRIGHT ================================
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=50)
            context = browser.new_context()

            # Clear and add cookies
            context.clear_cookies()
            try:
                context.add_cookies(cookies)
            except Exception:
                context.add_cookies([c for c in cookies])

            page = context.new_page()
            page.set_default_timeout(60000)

            # ================================ NAVIGATE TO JIRA ================================
            logger.console("Navigating to Jira...")

            try:
                page.goto("https://automationbot999.atlassian.net", wait_until="domcontentloaded")
                if "login" in page.url.lower():
                    raise TimeoutError("Cookie session expired")
            except TimeoutError:
                logger.console("Cookie expired → redirecting to login")
                page.goto("https://id.atlassian.com/login", wait_until="domcontentloaded")
                raise

            # ================================ OPEN PROJECT ================================
            logger.console("Opening project...")
            try:
                project = page.locator("a[href*='/browse/DEMO']").first
                project.wait_for(state="visible", timeout=35000)
                project.click()
                page.wait_for_timeout(1000)
            except Exception:
                logger.console("Project link not found, continuing...")

            # ================================ OPEN ISSUE DIRECTLY ================================
            logger.console(f"Opening Issue {issue_key} ...")

            page.goto(
                f"https://automationbot999.atlassian.net/browse/{issue_key}",
                wait_until="domcontentloaded"
            )

            # Wait for React to fully render header
            try:
                page.wait_for_selector(
                    "[data-testid='issue.views.issue-base.foundation.summary.heading']",
                    timeout=60000
                )
            except TimeoutError:
                logger.console(" Issue header did not load — possible redirect or cookie problem")
                logger.console("Final URL: " + page.url)
                raise

            # Also ensure issue key is present in DOM
            expect(page.locator(f"text={issue_key}").first).to_be_visible(timeout=60000)

            # After this point, page == page1 in previous version
            page1 = page

            # ================================ ASSIGN TO ME ================================
            logger.console("Assigning issue...")
            page1.wait_for_timeout(1000)

            assignee_btn = page1.get_by_test_id("issue-field-assignee-assign-to-me.ui.assign-to-me.link")

            if assignee_btn.is_visible():
                assignee_btn.click()
                logger.console(f" Assigned to: {assignee_name}")
            else:
                logger.console("Assign to Me button not visible")

            # ================================ SET PRIORITY ================================
            logger.console("Setting priority...")
            page1.get_by_test_id("issue-field-priority-readview-full.ui.priority.wrapper").click()

            pr_option = page1.get_by_text(issue_priority, exact=True)
            pr_option.wait_for(state="visible", timeout=15000)
            pr_option.click()

            expect(
                page1.get_by_test_id("issue-field-priority-readview-full.ui.priority.wrapper").locator("span")
            ).to_contain_text(issue_priority)

            logger.console(f" Priority set: {issue_priority}")

            # ================================ SET LABEL ================================
            logger.console("Setting label...")

            label_container = page1.get_by_test_id("issue.views.issue-base.context.labels")

            label_container.get_by_test_id(
                "issue-field-inline-edit-read-view-container.ui.container"
            ).click()

            label_input = page1.get_by_role("combobox", name="Labels")
            label_input.fill(label)
            page1.keyboard.press("Enter")
            page1.wait_for_timeout(600)

            # Commit label
            page1.get_by_test_id("issue.views.issue-base.foundation.summary.heading").click()
            page1.wait_for_timeout(600)

            expect(label_container).to_contain_text(label)
            logger.console(f"Label set: {label}")

            # ================================ ADD COMMENT ================================
            logger.console("Adding comment...")

            page1.get_by_test_id("issue-activity-feed.ui.buttons.Comments").click()

            comment_placeholder = page1.get_by_test_id(
                "canned-comments.common.ui.comment-text-area-placeholder.textarea"
            )

            comment_placeholder.scroll_into_view_if_needed()
            page1.wait_for_timeout(500)

            # Avoid toolbar overlap
            page1.evaluate("el => el.click()", comment_placeholder.element_handle())

            editor = page1.locator('div[role="textbox"]')
            editor.wait_for(state="visible", timeout=10000)

            editor.fill(comment_text)

            page1.get_by_test_id("comment-save-button").click()

            expect(page1.get_by_text(comment_text)).to_be_visible(timeout=8000)
            logger.console(f"Comment added: {comment_text}")

            # ================================ RESULTS ================================
            logger.console(
                f"UI Updates Complete:\n"
                f"- Assignee: {assignee_name}\n"
                f"- Priority: {issue_priority}\n"
                f"- Label: {label}\n"
                f"- Comment: {comment_text}"
            )

            context.close()
            browser.close()

            return assignee_name, issue_priority, label, comment_text
