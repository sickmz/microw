import logging

from dotenv import load_dotenv

from os import getenv, environ

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Load env vars
load_dotenv()
TELEGRAM_BOT_TOKEN: str = environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_USER_ID: str = environ["TELEGRAM_USER_ID"]
REMOTE_SPREADSHEET_ID: str = getenv("REMOTE_SPREADSHEET_ID")
REMOTE_EXPENSE_SHEET: str = getenv("REMOTE_EXPENSE_SHEET")

# Pagination
ITEMS_PER_PAGE = 5
