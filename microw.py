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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()
env_vars = dotenv_values()

SPREADSHEET_ID = env_vars.get("SPREADSHEET_ID")
BOT_TOKEN = env_vars.get("BOT_TOKEN")
EXPENSE_SHEET = env_vars.get("EXPENSE_SHEET")
USER_ID = env_vars.get("USER_ID")

CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, CHOOSING_PRICE, CHOOSING_EXPENSE_TO_DELETE = range(5)

reply_keyboard = [
    ["🍕 Add expense", "🍷 Delete expense"],
    ["❤️ Summary"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

categories = {
  'Home': ['Gas', 'Light', 'Water', 'Tari', 'Rent', 'Products'],
  'Food': ['Market', 'Delivery', 'Gastronomy'],
  'Subscriptions': ['Fastweb', 'Ho', 'Everli', 'Prime'],
}

def dynamic_kb(options: list) -> ReplyKeyboardMarkup:
    keyboard = []
    for i in range(0, len(options), 3):
        line = options[i:i+3]
        if len(line) < 3:
            line += [''] * (3 - len(line))
        keyboard.append(line)
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def static_kb(options: list) -> ReplyKeyboardMarkup:
    keyboard = [[option] for option in options]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    if str(update.message.from_user.id) != str(USER_ID):
        await update.message.reply_text(f"You're not authorized. ⛔")
        return ConversationHandler.END

    await update.message.reply_text(
        "Hi! I'm microw. "
        "What can I do for you?",
        reply_markup=markup,
    )

    return CHOOSING

async def start_add_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for category."""
    await update.message.reply_text(
        "Select a category:", reply_markup=dynamic_kb(list(categories.keys())),
        )

    return CHOOSING_CATEGORY

async def choose_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for subcategory."""
    selected_category = update.message.text
    subcategories = categories[selected_category]
    await update.message.reply_text(
        f"Choose a subcategory for {selected_category}:", reply_markup=dynamic_kb(subcategories)
    )
    context.user_data["selected_category"] = selected_category
    
    return CHOOSING_SUBCATEGORY

async def choose_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for the price."""
    selected_subcategory = update.message.text
    selected_category = context.user_data["selected_category"]
    context.user_data["selected_subcategory"] = selected_subcategory

    await update.message.reply_text("Enter the price for this item:", forceReplay=True)

    return CHOOSING_PRICE

async def save_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save and restart the context"""
    price = float(update.message.text.replace(',', '.'))
    selected_category = context.user_data["selected_category"]
    selected_subcategory = context.user_data["selected_subcategory"]
    await update.message.reply_text(
        f"Expense saved! ✨ \n\n"
        f"Category: {selected_category}\n"
        f"Subcategory: {selected_subcategory}\n"
        f"Price: {price} €",
        disable_notification=True,
    )

    ws = gspread.service_account(filename='credentials.json').open_by_key(SPREADSHEET_ID).worksheet(EXPENSE_SHEET)
    ws.append_row([datetime.datetime.now().strftime("%B"), selected_category, selected_subcategory, price, datetime.datetime.now().strftime("%d/%m/%Y")])

    return await start(update, context)

async def start_delete_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user what expense he wants to eliminate."""
    ws = gspread.service_account(filename='credentials.json').open_by_key(SPREADSHEET_ID).worksheet(EXPENSE_SHEET)
    num_rows = len(ws.col_values(1)) 

    last_five_rows = ws.get(f"A{num_rows - 4}:E{num_rows}")
    row_indices = list(range(num_rows - 4, num_rows + 1))
    combined_data = [[str(index)] + row for index, row in zip(row_indices, last_five_rows)]

    expense_options = [
        f"ID: {data[0]} ❌ {data[2]}/{data[3]} -> {data[4]} € ❌"
        for data in combined_data
    ]

    await update.message.reply_text("Choose an expense to delete:", reply_markup=static_kb(expense_options))

    return CHOOSING_EXPENSE_TO_DELETE

async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete the selected expense."""
    selected_option = update.message.text
    selected_id = int(selected_option.split(":")[1].strip().split(" ")[0])
    ws = gspread.service_account(filename='credentials.json').open_by_key(SPREADSHEET_ID).worksheet(EXPENSE_SHEET)

    try:
        ws.delete_rows(selected_id)
        await update.message.reply_text("Expense deleted successfully. ✅")
    except gspread.exceptions.APIError as e:
        await update.message.reply_text("An error occurred. Please try again.")

    return await start(update, context)

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get all the expenses and do some magic calculations."""
    await update.message.reply_text("Work in progress..")
    return await start(update, context)

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Action cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return await start(update, context)

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler("start", start)],
        states = {
            CHOOSING: [
                MessageHandler(filters.Regex("^(🍕 Add expense)$"), start_add_process),
                MessageHandler(filters.Regex("^(🍷 Delete expense)$"), start_delete_process),
                MessageHandler(filters.Regex("^(❤️ Summary)$"), show_summary),
            ],
            CHOOSING_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_subcategory)],
            CHOOSING_SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_price)],
            CHOOSING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_item)],
            CHOOSING_EXPENSE_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_expense)],
        },
        fallbacks = [CommandHandler("cancel", fallback)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()