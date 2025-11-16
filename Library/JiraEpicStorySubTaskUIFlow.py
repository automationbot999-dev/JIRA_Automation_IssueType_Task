import os
import json
from robot.api.deco import keyword, library
from playwright.sync_api import sync_playwright, expect, TimeoutError
from robot.api import logger


@library
class JiraEpicStorySubTaskUIFlow:
    """
    Robot library for creating a Story under an Epic using Jira UI (Playwright).
    """

    @keyword("Run Epic UI Flow")
    def run_epic_ui_flow(self, epic_key):
        """
        UI Flow:
        - Load Jira using stored session cookies
        - Validate Epic page
        - Create Story under Epic using inline child work item flow
        - Return STORY_KEY
        """

        # Load Jira cookies from file
        cookie_path = os.path.join(os.path.dirname(__file__), "jira_cookies.json")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError("jira_cookies.json not found in Library folder")

        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        # Start Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=100)

            # Create clean browser context
            context = browser.new_context()

            # FIX: Always clear old cookies
            context.clear_cookies()

            # FIX: Load cookies safely
            try:
                context.add_cookies(cookies)
            except Exception as e:
                logger.console(f" Cookie load issue: {e}")
                logger.console("Proceeding without valid cookies...")

            page = context.new_page()

            # FIX: Increased timeout to 60 seconds for Docker
            page.set_default_timeout(60000)

            logger.console("Navigating to Jira...")

            # ----- FIRST ATTEMPT -----
            try:
                page.goto("https://automationbot999.atlassian.net",
                          wait_until="domcontentloaded")

                if "login" in page.url:
                    raise TimeoutError("Session expired → login required")

            except TimeoutError:
                logger.console("Cookie session expired — retrying with login page")
                page.goto("https://id.atlassian.com/login", wait_until="domcontentloaded")
                raise

            # ================================
            # Open Project
            # ================================
            logger.console("Opening demo project...")

            try:
                project = page.locator("a[href*='/browse/DEMO']").first
                project.wait_for(state="visible", timeout=25000)
                project.click()
                page.wait_for_timeout(1500)
            except TimeoutError:
                logger.console("Project link not detected — navigating directly to epic")

            # ================================
            # Open Epic Page
            # ================================
            logger.console(f"Opening Epic → {epic_key}")
            page.goto(f"https://automationbot999.atlassian.net/browse/{epic_key}",
                      wait_until="domcontentloaded")

            breadcrumb = page.get_by_test_id(
                "issue.views.issue-base.foundation.breadcrumbs.current-issue.item"
            ).locator("span")

            breadcrumb.wait_for(state="visible", timeout=25000)
            expect(breadcrumb).to_contain_text(epic_key)
            logger.console(f" Epic {epic_key} is visible on UI")

            # ================================
            # Create Story under Epic
            # ================================
            logger.console("Creating Story under Epic...")

            # ---------- DOCKER-SAFE LOCATOR BLOCK ----------
            for attempt in range(5):
                try:
                    add_child_btn = page.locator(
                        "//span[text()='Add child work item']/ancestor::button"
                    )

                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(500)

                    add_child_btn.wait_for(state="visible", timeout=10000)

                    # JS scroll — always reliable in headless Docker
                    page.evaluate("el => el.scrollIntoView()", add_child_btn.element_handle())
                    page.wait_for_timeout(300)

                    add_child_btn.hover()
                    page.wait_for_timeout(300)

                    #logger.console("Add child work item button ready")
                    break

                except Exception:
                    logger.console(f"Retry {attempt+1}/5 — element unstable, retrying...")
                    page.wait_for_timeout(700)
            else:
                raise TimeoutError(" Add child work item button never stabilized in DOM")
            # --------------------------------------------------

            # Try clicking 3 different ways
            clicked = False
            for method in ["click", "dblclick", "click(force=True)"]:
                try:
                    if method == "click":
                        add_child_btn.click()
                    elif method == "dblclick":
                        add_child_btn.dblclick()
                    else:
                        add_child_btn.click(force=True)

                    page.wait_for_timeout(800)

                    panel_open = (
                        page.locator(
                            "//input[@data-testid='issue-view-common-views.child-issues-panel.inline-create.summary-textfield']"
                        ).is_visible()
                        or page.locator("button[aria-label='Select work type']").is_visible()
                        or page.locator("//button[contains(.,'Cancel')]").is_visible()
                    )

                    if panel_open:
                        clicked = True
                        break

                except Exception:
                    pass

            if not clicked:
                raise TimeoutError("Failed to open 'Add child work item' panel")

            # Open Type dropdown
            work_type_btn = page.locator("button[aria-label='Select work type']").first
            work_type_btn.wait_for(state="visible", timeout=15000)
            work_type_btn.click()

            # Select STORY
            story_option = page.locator(
                "//div[@role='group']//button[.//span[contains(.,'Story')]]"
            ).first

            story_option.wait_for(state="visible", timeout=10000)
            story_option.click()

            # Enter summary
            summary_input = page.locator(
                "//input[@data-testid='issue-view-common-views.child-issues-panel.inline-create.summary-textfield']"
            )
            summary_input.wait_for(state="visible", timeout=15000)
            summary_input.fill("User story created using UI")
            summary_input.press("Enter")

            # Extract story key
            summary_text = "User story created using UI"

            story_row = page.locator(
                "//tr[@data-testid='native-issue-table.ui.issue-row']"
                f"[.//a[contains(text(), '{summary_text}')]]"
            )
            story_row.wait_for(state="visible", timeout=25000)

            story_key_el = story_row.locator(
                "a[data-testid='native-issue-table.common.ui.issue-cells.issue-key.issue-key-cell']"
            )
            story_key_el.wait_for(state="visible", timeout=25000)

            story_key = story_key_el.inner_text().strip()

            context.close()
            browser.close()

            return story_key
