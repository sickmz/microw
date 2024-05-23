import logging
from dotenv import load_dotenv, dotenv_values

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()
env_vars = dotenv_values()
BOT_TOKEN = env_vars.get("BOT_TOKEN")
USER_ID = env_vars.get("USER_ID")
SPREADSHEET_ID = env_vars.get("SPREADSHEET_ID")
EXPENSE_SHEET = env_vars.get("EXPENSE_SHEET")
LOCAL_EXPENSE_PATH = env_vars.get("LOCAL_EXPENSE_PATH")

# Pagination
ITEMS_PER_PAGE = 5
