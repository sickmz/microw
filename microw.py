import logging
import os
from dotenv import load_dotenv, dotenv_values 
import gspread
import datetime

from typing import Dict
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

# Logging settings
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Definition of state names
CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, ENTERING_PRICE = range(3)

# Secrets
load_dotenv()
env_vars = dotenv_values()


SPREADSHEET_ID = env_vars.get("SPREADSHEET_ID")
BOT_TOKEN = env_vars.get("BOT_TOKEN")
EXPENSE_SHEET = env_vars.get("EXPENSE_SHEET")
USER_ID = env_vars.get("USER_ID")

# Keyboard with categories and respective subcategories
categories = {
  'Home': ['Gas', 'Light', 'Water', 'Tari', 'Rent', 'Products'],
  'Food': ['Market', 'Delivery', 'Gastronomy'],
  'Subscriptions': ['Fastweb', 'Ho', 'Everli', 'Prime'],
}

# Function to dynamically build the keyboard
def build_keyboard(options: list) -> ReplyKeyboardMarkup:
    keyboard = []
    for i in range(0, len(options), 3):
        line = options[i:i+3]
        if len(line) < 3:
            line += [''] * (3 - len(line))
        keyboard.append(line)
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

# Function to handle bot startup
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if str(update.message.from_user.id) != str(USER_ID):
        await update.message.reply_text(f"⛔ You're not authorized! ⛔")
        await context.bot.send_message(USER_ID, f"⛔ Unauthorized access attempted ⛔ \n\n - username: {update.message.from_user.name} \n - id: {update.message.from_user.id}")
        return ConversationHandler.END

    await update.message.reply_text(
        "Select a category:", reply_markup=build_keyboard(list(categories.keys())),
        disable_notification=True,
    )

    return CHOOSING_CATEGORY

# Function to handle conversation interruption
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Action cancelled.", reply_markup=ReplyKeyboardRemove(), 
    disable_notification=True,
    )
    context.user_data.clear()
    
    return await start(update, context)  

# Function to handle category selection
async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_category = update.message.text
    subcategories = categories[selected_category]
    await update.message.reply_text(
        f"Choose a subcategory for {selected_category}:",
        reply_markup=build_keyboard(subcategories),
        disable_notification=True,
    )
    context.user_data["selected_category"] = selected_category
    
    return CHOOSING_SUBCATEGORY


# Function to handle subcategory selection
async def choose_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_subcategory = update.message.text
    selected_category = context.user_data["selected_category"]
    context.user_data["selected_subcategory"] = selected_subcategory
    await update.message.reply_text("Enter the price for this item:", 
    disable_notification=True,
    )

    return ENTERING_PRICE

# Function to handle price entry
async def enter_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price_text = update.message.text
    try:
        price = float(price_text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text("❌ The entered price is not valid. Please enter a number.")
        return await start(update, context) 
        
    selected_category = context.user_data["selected_category"]
    selected_subcategory = context.user_data["selected_subcategory"]
    await update.message.reply_text(
        f"Expense saved! ✨ \n\nCategory: {selected_category}\nSubcategory: {selected_subcategory}\nPrice: {price}" + " €",
        disable_notification=True,
    )

    gc = gspread.service_account(filename='credentials.json') 
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(EXPENSE_SHEET)
    ws.append_row([datetime.datetime.now().strftime("%B"), selected_category, selected_subcategory, price, datetime.datetime.now().strftime("%d/%m/%Y")])

    return await start(update, context)

# Main function to start the bot
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_category)],
            CHOOSING_SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_subcategory)],
            ENTERING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()