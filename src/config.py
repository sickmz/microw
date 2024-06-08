import logging

from dotenv import dotenv_values, load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()
env_vars = dotenv_values()
TELEGRAM_BOT_TOKEN = env_vars.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = env_vars.get("TELEGRAM_USER_ID")
REMOTE_SPREADSHEET_ID = env_vars.get("REMOTE_SPREADSHEET_ID")
REMOTE_EXPENSE_SHEET = env_vars.get("REMOTE_EXPENSE_SHEET")

# Pagination
ITEMS_PER_PAGE = 5
