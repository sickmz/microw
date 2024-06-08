from telegram import ReplyKeyboardMarkup

# Constants to manage the state
(
    CHOOSING,
    CHOOSING_CATEGORY,
    CHOOSING_SUBCATEGORY,
    CHOOSING_PRICE,
    CHOOSING_ITEM_TO_DELETE,
    CHOOSING_CHART,
    CHOOSING_BUDGET,
    CHOOSING_BUDGET_CATEGORY,
    CHOOSING_BUDGET_AMOUNT,
) = range(9)

LOCAL_BUDGET_PATH = "./spreadsheets/budget.xlsx"
LOCAL_EXPENSE_PATH = "./spreadsheets/expenses.xlsx"
LOCAL_CHART_PATH = "./charts"
LOCAL_SETTINGS_PATH = "./settings.json"

# Define reply keyboard
reply_keyboard = [
    ["✏️ Add", "❌ Delete", "📊 Charts"],
    ["📋 List", "💰 Budget", "⚙️ Settings"],
]
markup = ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=False, resize_keyboard=True
)

# Define categories
categories = {
    "Home": ["Gas", "Light", "Water", "Tari", "Rent", "Products"],
    "Food": ["Market", "Delivery", "Gastronomy"],
    "Subscription": ["Fastweb", "Ho", "Everli", "Prime"],
}
