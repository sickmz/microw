from telegram import ReplyKeyboardMarkup

# Constants to manage the state
CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, \
    CHOOSING_PRICE, CHOOSING_ITEM_TO_DELETE, CHOOSING_CHART = range(6)

# Define reply keyboard
reply_keyboard = [
    ["✏️ Add", "❌ Delete", "📊 Charts"],
    ["📋 List", "🔄 Reset", "⚙️ Settings"],
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
