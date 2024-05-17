import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import datetime
import calendar
import seaborn as sns
from cachetools import TTLCache
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv, dotenv_values

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARN)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
env_vars = dotenv_values()
SPREADSHEET_ID = env_vars.get("SPREADSHEET_ID")
BOT_TOKEN = env_vars.get("BOT_TOKEN")
EXPENSE_SHEET = env_vars.get("EXPENSE_SHEET")
USER_ID = env_vars.get("USER_ID")

# Set up cache
cache = TTLCache(maxsize=100, ttl=86400)

# Constants for conversation steps
CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, CHOOSING_PRICE, CHOOSING_ITEM_TO_DELETE, CHOOSING_CHART = range(6)

# Define reply keyboard
reply_keyboard = [
    ["✏️ Add", "❌ Delete", "📊 Charts"],
    ["📋 List", "🔄 Reset", "❓ Help"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

# Define categories
categories = {
    'Home': ['Gas', 'Light', 'Water', 'Tari', 'Rent', 'Products'],
    'Food': ['Market', 'Delivery', 'Gastronomy'],
    'Subscriptions': ['Fastweb', 'Ho', 'Everli', 'Prime'],
}

# Helper function to build keyboard
def build_keyboard(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(option, callback_data=option)] for option in options])

# Get Google Sheet worksheet
def get_worksheet(spreadsheet_id, worksheet_name):
    key = f"{spreadsheet_id}:{worksheet_name}"
    if key not in cache:
        gc = gspread.service_account(filename='credentials.json')
        cache[key] = gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    return cache[key]

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if str(update.effective_user.id) != str(USER_ID):
        await update.message.reply_text("You're not authorized. ⛔")
        return ConversationHandler.END
    await update.effective_message.reply_text("Hi! I'm microw. What can I do for you?", reply_markup=markup)

    return CHOOSING

# Ask for category
async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Select a category:", reply_markup=build_keyboard(categories.keys()))

    return CHOOSING_CATEGORY

# Ask for subcategory
async def ask_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['selected_category'] = update.callback_query.data
    await update.callback_query.message.edit_text("Select a subcategory:", reply_markup=build_keyboard(categories[context.user_data['selected_category']]))

    return CHOOSING_SUBCATEGORY

# Ask for price
async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["selected_subcategory"] = update.callback_query.data
    await update.callback_query.message.edit_text("Enter the price for this item:")

    return CHOOSING_PRICE

# Save expense on Google Sheet
async def save_on_google_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.replace(',', '.'))
        category = context.user_data["selected_category"]
        subcategory = context.user_data["selected_subcategory"]
        ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
        ws.append_row([datetime.datetime.now().strftime("%B"), category, subcategory, price, datetime.datetime.now().strftime('%d/%m/%Y')])
        await update.message.reply_text(f"<b>Expense saved 📌</b>\n\n<b>Category:</b> {category}\n<b>Subcategory:</b> {subcategory}\n<b>Price:</b> {price} €", parse_mode='HTML')
    except ValueError:
        await update.message.reply_text("Please enter a valid price. 🚨")

    return await start(update, context)

# Deleting an expense
async def ask_deleting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    num_rows = len(ws.col_values(1))
    rows_to_display = min(num_rows, 5)
    last_rows = ws.get(f"A{num_rows - rows_to_display + 1}:E{num_rows}")
    row_indices = list(range(num_rows - rows_to_display + 1, num_rows + 1))
    combined_data = [[str(index)] + row for index, row in zip(row_indices, last_rows)]
    expense_options = [[InlineKeyboardButton(f"🗑️ {data[2]}/{data[3]}: {data[4]} €", callback_data=str(data[0]))] for data in combined_data]
    await update.message.reply_text("Choose an expense to delete:", reply_markup=InlineKeyboardMarkup(expense_options))

    return CHOOSING_ITEM_TO_DELETE

# Delete expense from Google Sheet
async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_id = int(update.callback_query.data)
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    try:
        ws.delete_rows(selected_id)
        await update.callback_query.message.edit_text("Expense deleted successfully. ✅")
    except gspread.exceptions.APIError:
        await update.callback_query.message.reply_text("An error occurred. Please try again.")

    return await start(update, context)

async def make_charts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chart_buttons = [
        [InlineKeyboardButton("Expense by category (yearly)", callback_data="chart_yearly")],
        [InlineKeyboardButton("Expense by category (monthly)", callback_data="chart_monthly")],
        [InlineKeyboardButton("Trend top 3 categories (monthly)", callback_data="chart_trend")],
        [InlineKeyboardButton("Heatmap expense intensity (monthly)", callback_data="chart_heatmap")]
    ]
    await update.message.reply_text("Select a chart to view:", reply_markup=InlineKeyboardMarkup(chart_buttons))

    return CHOOSING_CHART
async def show_yearly_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    values = ws.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    df['Price'] = df['Price'].str.replace(',', '.').astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    
    await save_pie_chart(df, 'charts/expense_by_category_by_year.png')
    await update.callback_query.message.reply_photo(open('charts/expense_by_category_by_year.png', 'rb'), caption="Expense by category (yearly)")

    return await start(update, context)

async def save_pie_chart(df, filename):
    expenses_by_category = df.groupby('Category')['Price'].sum().reset_index()
    plt.figure(figsize=(10, 6))
    pie = plt.pie(expenses_by_category['Price'], autopct=lambda p: f'{p:.1f}% ({p*sum(expenses_by_category["Price"])/100:.2f} €)' if p > 5 else '', startangle=90)
    plt.legend(pie[0], expenses_by_category['Category'], loc="best")
    plt.axis('equal')
    plt.savefig(filename)
    plt.close()

async def show_trend_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    values = ws.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    df['Price'] = df['Price'].str.replace(',', '.').astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_trend_chart(df, 'charts/expense_trend_top_categories_by_month.png')
    await update.callback_query.message.reply_photo(open('charts/expense_trend_top_categories_by_month.png', 'rb'), caption="Trend top 3 categories (monthly)")

    return await start(update, context)

async def show_monthly_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    values = ws.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    df['Price'] = df['Price'].str.replace(',', '.').astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_stacked_bar_chart(df, 'charts/monthly_expenses_by_category.png')
    await update.callback_query.message.reply_photo(open('charts/monthly_expenses_by_category.png', 'rb'), caption="Expense by category (monthly)")

    return await start(update, context)

async def save_trend_chart(df, filename):
    df['Month'] = df['Date'].dt.month
    top_categories = df.groupby('Category')['Price'].sum().nlargest(3).index
    top_categories_data = df[df['Category'].isin(top_categories)]
    expenses_by_month_category = top_categories_data.groupby(['Month', 'Category'])['Price'].sum().unstack(fill_value=0)
    plt.figure(figsize=(10, 6))
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    ax = expenses_by_month_category.plot(kind='line', marker='o', ax=plt.gca())
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names, rotation=45, ha='right')
    ax.set_xlabel('') 
    plt.legend(title='Category', loc='upper right')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

async def save_stacked_bar_chart(df, filename):
    df['Month'] = df['Date'].dt.strftime('%B')
    monthly_expenses = df.groupby(['Month', 'Category'])['Price'].sum().unstack().fillna(0)
    months_order = list(calendar.month_name[1:])
    monthly_expenses = monthly_expenses.reindex(months_order)
    plt.figure(figsize=(12, 8))
    ax = monthly_expenses.plot(kind='bar', stacked=True, width=0.8, zorder=3)
    ax.set_xticklabels(months_order, rotation=45, ha='right')
    ax.set_xlabel('') 
    plt.legend(loc='upper right')
    plt.grid(True, zorder=0)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

async def show_heatmap_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    values = ws.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    df['Price'] = df['Price'].str.replace(',', '.').astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_heatmap(df, 'charts/heatmap_expense_intensity.png')
    await update.callback_query.message.reply_photo(open('charts/heatmap_expense_intensity.png', 'rb'), caption="Heatmap of expense intensity (monthly)")

    return await start(update, context)

async def save_heatmap(df, filename):
    df['Month'] = df['Date'].dt.strftime('%B')
    heatmap_data = df.pivot_table(values='Price', index='Category', columns='Month', aggfunc='sum', fill_value=0)
    existing_months = [month for month in calendar.month_name[1:] if month in heatmap_data.columns]
    heatmap_data = heatmap_data[existing_months]
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, fmt=".2f", annot=True, cmap="YlGnBu")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# List of expenses
async def make_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ws = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
    values = ws.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    df['Price'] = df['Price'].str.replace(',', '.').astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    current_year = datetime.datetime.now().year
    df_current_year = df[df['Date'].dt.year == current_year]

    message = ""
    grouped = df_current_year.groupby([df_current_year['Date'].dt.month, 'Category'])['Price'].sum()
    total_per_month = df_current_year.groupby(df_current_year['Date'].dt.month)['Price'].sum()
    for month in range(1, datetime.datetime.now().month + 1):
        month_name = calendar.month_name[month]
        message += f"\n<b>{month_name}:</b>\n"
        if month in grouped.index.get_level_values(0):
            for category, amount in grouped[month].items():
                message += f"  - {category}: {amount:.2f} €\n"
        total = total_per_month.get(month, 0)
        message += f"  <b>Total:</b> {total:.2f} €\n"
    await update.message.reply_text(message, parse_mode='HTML')

    return await start(update, context)

# Help message
async def ask_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_text = (
        "Available commands:\n\n"
        "/start: Start the bot.\n\n"
        "➕ Add: Add a new expense.\n"
        "❌ Delete: Delete an existing expense.\n"
        "📊 Charts: View charts of expenses.\n"
        "📋 List: Displays a summary of expenses.\n"
        "🔄 Reset: Reset the conversation.\n"
        "❓ Help: Display this help message."
    )
    await update.message.reply_text(help_text)

    return await start(update, context)

# Invalid action handler
async def invalid_transition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Invalid action. One thing at a time..")

    return await start(update, context)

# Reset conversation
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    return await start(update, context)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^✏️ Add$"), ask_category),
                MessageHandler(filters.Regex("^❌ Delete$"), ask_deleting),
                MessageHandler(filters.Regex("^📊 Charts$"), make_charts),
                MessageHandler(filters.Regex("^📋 List$"), make_list),
                MessageHandler(filters.Regex("^❓ Help$"), ask_help),
            ],
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(ask_subcategory), 
                MessageHandler(filters.Regex("^(❌ Delete|📊 Charts|📋 List|❓ Help)$"), invalid_transition)],
            CHOOSING_SUBCATEGORY: [
                CallbackQueryHandler(ask_price), 
                MessageHandler(filters.Regex("^(❌ Delete|📊 Charts|📋 List|❓ Help)$"), invalid_transition)],
            CHOOSING_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_on_google_sheet), 
                MessageHandler(filters.Regex("^(❌ Delete|📊 Charts|📋 List|❓ Help)$"), invalid_transition)],
            CHOOSING_ITEM_TO_DELETE: [
                CallbackQueryHandler(delete_expense), 
                MessageHandler(filters.Regex("^(✏️ Add|📊 Charts|📋 List|❓ Help)$"), invalid_transition)],
            CHOOSING_CHART: [
                CallbackQueryHandler(show_yearly_chart, pattern="^chart_yearly$"),
                CallbackQueryHandler(show_monthly_chart, pattern="^chart_monthly$"),
                CallbackQueryHandler(show_trend_chart, pattern="^chart_trend$"),
                CallbackQueryHandler(show_heatmap_chart, pattern="^chart_heatmap$"),
                MessageHandler(filters.Regex("^(✏️ Add|❌ Delete|📋 List|❓ Help)$"), invalid_transition)],         
        },
        fallbacks=[MessageHandler(filters.Regex("^🔄 Reset$"), fallback)],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
