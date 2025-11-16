import os
import json
from robot.api.deco import keyword, library
from playwright.sync_api import sync_playwright, expect, TimeoutError
from robot.api import logger
import time


@library
class JiraEpicTaskUIFlow:
    """
    Robot library for creating a TASK under an Epic using Jira UI (Playwright).
    """

    @keyword("Run Epic Task UI Flow")
    def run_epic_task_ui_flow(self, epic_key):
        """
        UI Flow:
        - Load Jira using stored session cookies
        - Navigate to Epic
        - Create Task under Epic using inline child work item panel
        - Return TASK_KEY
        """

        # Load Jira cookies
        cookie_path = os.path.join(os.path.dirname(__file__), "jira_cookies.json")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError("jira_cookies.json not found in Library folder")

        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        # Start Playwright
        with sync_playwright() as p:
            # headless True recommended for container runs
            browser = p.chromium.launch(headless=True, slow_mo=60)

            # Fresh browser context
            context = browser.new_context()

            # Always clear old cookies
            try:
                context.clear_cookies()
            except Exception:
                # not fatal; log and continue
                logger.console("Warning: context.clear_cookies() failed, continuing")

            # Safe cookie loading
            try:
                context.add_cookies(cookies)
            except Exception as e:
                try:
                    context.add_cookies([c for c in cookies])
                except Exception as e2:
                    logger.console(f"Cookie load issue: {e} / {e2}")
                    logger.console("Proceeding without valid cookies...")

            page = context.new_page()

            # Increase timeout globally for slow CI/container environments
            page.set_default_timeout(60000)

            logger.console("Navigating to Jira...")

            # ----- FIRST ATTEMPT -----
            try:
                page.goto("https://automationbot999.atlassian.net", wait_until="domcontentloaded")
                # If Atlassian redirected to login, treat as expired cookie
                if "login" in page.url.lower():
                    logger.console("Invalid/expired session detected → redirected to login")
                    raise TimeoutError("Session expired")
            except TimeoutError:
                logger.console("Cookie session expired — navigating to login page to surface issue")
                try:
                    page.goto("https://id.atlassian.com/login", wait_until="domcontentloaded")
                except Exception:
                    # ignore further errors here; raising to indicate session/login required
                    pass
                raise

            # ================================
            # Open Epic Page
            # ================================
            logger.console(f"Opening Epic → {epic_key}")
            page.goto(f"https://automationbot999.atlassian.net/browse/{epic_key}", wait_until="domcontentloaded")

            # Validate epic page
            breadcrumb = page.get_by_test_id(
                "issue.views.issue-base.foundation.breadcrumbs.current-issue.item"
            ).locator("span")

            breadcrumb.wait_for(state="visible", timeout=30000)
            expect(breadcrumb).to_contain_text(epic_key)
            logger.console(f" Epic {epic_key} is visible on UI")

            # ================================
            # Helper: robust click on locator with retries and JS fallback
            # ================================
            def robust_click_locator(get_locator_func, timeout=30000):
                """
                get_locator_func: callable returning a locator when called.
                Tries multiple click strategies and re-queries locator each try.
                """
                start = time.time()
                last_err = None
                while time.time() - start < (timeout / 1000.0):
                    try:
                        loc = get_locator_func()
                        # ensure visible & attached
                        loc.wait_for(state="visible", timeout=5000)
                        # try normal click first
                        try:
                            loc.scroll_into_view_if_needed()
                            loc.click()
                            return True
                        except Exception as e_click:
                            last_err = e_click
                        # try dblclick
                        try:
                            loc.dblclick()
                            return True
                        except Exception:
                            pass
                        # try force click
                        try:
                            loc.click(force=True)
                            return True
                        except Exception:
                            pass
                        # try JS click on element handle
                        try:
                            handle = loc.element_handle(timeout=2000)
                            if handle:
                                page.evaluate("el => el.click()", handle)
                                return True
                        except Exception:
                            pass
                    except Exception as e:
                        last_err = e

                    # small backoff and then re-query
                    time.sleep(0.6)

                # final attempt: log and raise
                logger.console(f"robust_click_locator exhausted; last error: {last_err}")
                return False

            # ================================
            # Helper: open inline panel (robust)
            # ================================
            def open_inline_panel():
                """
                Attempts to open the Add child work item inline panel using multiple techniques.
                Re-queries locator on every attempt to avoid 'element not attached' problems.
                """
                # define how to get locator (re-query each time)
                def get_add_btn():
                    return page.locator("//span[text()='Add child work item']/ancestor::button").first

                # Try clicking the add button robustly
                clicked = robust_click_locator(get_add_btn, timeout=30000)
                if not clicked:
                    # As extra fallback: try opening the "Create child" via alternate selector (icon-button)
                    def get_add_btn_alt():
                        return page.get_by_test_id("issue-view-common-views.button.icon-button.Create child")
                    clicked_alt = robust_click_locator(get_add_btn_alt, timeout=10000)
                    if not clicked_alt:
                        raise TimeoutError("Failed to open inline 'Add child work item' panel")

                # wait briefly for panel to appear
                time.sleep(0.6)

                # confirm panel presence via multiple indicators
                panel_indicators = [
                    "//input[@data-testid='issue-view-common-views.child-issues-panel.inline-create.summary-textfield']",
                    "button[aria-label='Select work type']",
                    "//button[contains(.,'Cancel')]"
                ]

                # wait loop for one of indicators
                start = time.time()
                while time.time() - start < 20:
                    try:
                        for sel in panel_indicators:
                            try:
                                if sel.startswith("//"):
                                    if page.locator(sel).is_visible():
                                        return True
                                else:
                                    if page.locator(sel).is_visible():
                                        return True
                            except Exception:
                                continue
                    except Exception:
                        pass
                    time.sleep(0.5)

                # last resort: try clicking Add again and then fail
                logger.console("Panel indicators not detected after initial click; retrying Add button once more")
                if not robust_click_locator(get_add_btn, timeout=8000):
                    raise TimeoutError("Failed to open inline 'Add child work item' panel after retries")

                # final wait
                time.sleep(0.8)
                # re-check indicators
                for sel in panel_indicators:
                    try:
                        if sel.startswith("//"):
                            if page.locator(sel).is_visible():
                                return True
                        else:
                            if page.locator(sel).is_visible():
                                return True
                    except Exception:
                        continue

                # give up
                raise TimeoutError("Failed to open inline 'Add child work item' panel")

            # ================================
            # Opening inline Task creation panel
            # ================================
            open_inline_panel()

            # If work type selector appears, choose Task
            try:
                work_type_btn = page.locator("button[aria-label='Select work type']").first
                if work_type_btn.is_visible():
                    work_type_btn.click()
                    task_btn = page.locator("//div[@role='group']//button[.//span[contains(.,'Task')]]").first
                    task_btn.wait_for(state="visible", timeout=15000)
                    task_btn.click()
                    logger.console(" Task work type selected")
                else:
                    logger.console(" Task selected automatically by default")
            except Exception:
                # If anything goes wrong selecting work type, continue if the summary input is visible
                logger.console("Work-type selection encountered an error; continuing if summary input is present")

            # ================================
            # Fill Task Summary
            # ================================
            task_summary = "Task created using UI"

            task_input = page.locator(
                "//input[@data-testid='issue-view-common-views.child-issues-panel.inline-create.summary-textfield']"
            )
            task_input.wait_for(state="visible", timeout=15000)
            try:
                task_input.fill(task_summary)
                task_input.press("Enter")
            except Exception:
                # fallback: use JS to set value and dispatch Enter
                try:
                    handle = task_input.element_handle(timeout=2000)
                    if handle:
                        page.evaluate(
                            "(el, val) => { el.focus(); el.value = val; el.dispatchEvent(new Event('input',{bubbles:true})); }",
                            handle,
                            task_summary,
                        )
                        page.keyboard.press("Enter")
                except Exception as e:
                    logger.console(f"Failed to fill summary via fallback: {e}")
                    raise

            # ================================
            # Extract Task Key
            # ================================
            task_row = page.locator(
                "//tr[@data-testid='native-issue-table.ui.issue-row']"
                "[.//a[contains(text(), 'Task created using UI')]]"
            )

            task_row.wait_for(state="visible", timeout=25000)

            task_key_el = task_row.locator(
                "a[data-testid='native-issue-table.common.ui.issue-cells.issue-key.issue-key-cell']"
            )
            task_key_el.wait_for(state="visible", timeout=10000)
            task_key = task_key_el.inner_text().strip()

            logger.console(f" Task created via UI: {task_key}")

            # Cleanup
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass

            return task_key
