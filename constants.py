from telegram import ReplyKeyboardMarkup

# Constants to manage the state
CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, \
    CHOOSING_PRICE, CHOOSING_ITEM_TO_DELETE, CHOOSING_CHART, \
        CHOOSING_BUDGET_ACTION, CHOOSING_BUDGET_CATEGORY, CHOOSING_BUDGET_AMOUNT = range(9)

BUDGET_PATH = 'spreadsheet/budget.xlsx'
EXPENSE_PATH = 'spreadsheet/expenses.xlsx'
SETTINGS_PATH = 'settings.json'

# Define reply keyboard
reply_keyboard = [
    ["✏️ Add", "❌ Delete", "📊 Charts"],
    ["📋 List", "💰 Budget", "⚙️ Settings"]
]
markup = ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=False, resize_keyboard=True
)

# Define categories
categories = {
    'Home': ['Gas', 'Light', 'Water', 'Tari', 'Rent', 'Products'],
    'Food': ['Market', 'Delivery', 'Gastronomy'],
    'Subscriptions': ['Fastweb', 'Ho', 'Everli', 'Prime'],
}
