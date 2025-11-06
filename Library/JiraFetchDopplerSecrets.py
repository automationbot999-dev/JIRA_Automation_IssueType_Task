from robot.api.deco import keyword
import os, json, subprocess
from dotenv import load_dotenv
from robot.libraries.BuiltIn import BuiltIn

class JiraFetchDopplerSecrets:

    @keyword("INITIALIZE SECRETS")
    def initialize_secrets(self):
        load_dotenv()
        token = os.getenv("JIRA_TOKEN")
        if not token:
            raise ValueError("JIRA_TOKEN is not set")

        result = subprocess.run([
            "curl", "-s",
            "-H", f"Authorization: Bearer {token}",
            "https://api.doppler.com/v3/configs/config/secrets/download?format=json"
        ], capture_output=True, text=True)

        if result.returncode != 0 or not result.stdout:
            raise RuntimeError("Failed to fetch secrets from Doppler")

        secrets = json.loads(result.stdout)
        username_email = secrets.get("USERNAME", "").strip()
        password_token = secrets.get("PASSWORD", "").strip()
        password_ui = secrets.get("UIPASSWORD", "").strip()

        if not username_email or not password_token:
            raise ValueError("USERNAME or PASSWORD not found in Doppler secrets")

        # Masked values for logging only
        masked_email = username_email[:3] + "..." + username_email.split("@")[-1]
        masked_token = password_token[:6] + "..." + password_token[-6:]
        masked_password_ui = password_ui[:3] + "..." + password_ui.split("@")[-1]

        BuiltIn().log(f"EMAIL set to: {masked_email}", level="INFO")
        BuiltIn().log(f"API_TOKEN set to: {masked_token}", level="INFO")
        BuiltIn().log(f"UI Password set to: {masked_password_ui}", level="INFO")

        # ✅ Set as environment variables for Python libraries like Playwright
        os.environ["EMAIL"] = username_email
        os.environ["API_TOKEN"] = password_token
        os.environ["UI_PASSWORD"] = password_ui

        # ✅ Also set for use inside Robot Framework directly
        BuiltIn().set_global_variable("${EMAIL}", username_email)
        BuiltIn().set_global_variable("${API_TOKEN}", password_token)
        BuiltIn().set_global_variable("${UI_PASSWORD}", password_ui)

        # Masked info only
        BuiltIn().log("EMAIL set to: *****")
        BuiltIn().log("API_TOKEN set to: *****")
        BuiltIn().log("UI Password set to: *****")
