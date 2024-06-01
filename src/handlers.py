import calendar
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import pandas as pd
from config import TELEGRAM_USER_ID, ITEMS_PER_PAGE

from constants import categories, markup
from constants import LOCAL_EXPENSE_PATH, LOCAL_BUDGET_PATH
from constants import CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, CHOOSING_PRICE, CHOOSING_ITEM_TO_DELETE, CHOOSING_CHART, CHOOSING_BUDGET, CHOOSING_BUDGET_CATEGORY, CHOOSING_BUDGET_AMOUNT

from utils import build_keyboard, get_local_expense_wb, save_settings, load_settings, is_local_expense_file_empty, get_local_budget_wb
from utils import set_budget, get_budget, update_spent, check_budget

from charts import save_pie_chart, save_stacked_bar_chart, save_trend_chart, save_heatmap


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /start command. Verifies user authorization and presents initial menu.
    """
    if str(update.effective_user.id) != str(TELEGRAM_USER_ID):
        await update.message.reply_text("You're not authorized. ⛔")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        "Hi! I'm microw. What can I do for you?",
        reply_markup=markup
    )
    return CHOOSING


async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to select an expense category.
    """
    await update.message.reply_text(
        "Select a category:",
        reply_markup=build_keyboard(categories.keys())
    )
    return CHOOSING_CATEGORY


async def ask_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Store selected category and prompt user to select a subcategory.
    """
    context.user_data['selected_category'] = update.callback_query.data
    await update.callback_query.message.edit_text(
        "Select a subcategory:",
        reply_markup=build_keyboard(
            categories[context.user_data['selected_category']])
    )
    return CHOOSING_SUBCATEGORY


async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Store selected subcategory and prompt user to enter the price.
    """
    context.user_data["selected_subcategory"] = update.callback_query.data
    await update.callback_query.message.edit_text(
        "Enter the price for this item:"
    )
    return CHOOSING_PRICE


async def save_on_local_spreadsheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save the entered expense to the local spreadsheet and provide user feedback.
    """
    try:
        price = float(update.message.text.replace(',', '.'))
        category = context.user_data["selected_category"]
        subcategory = context.user_data["selected_subcategory"]

        wb, ws = get_local_expense_wb()
        record_timestamp = datetime.datetime.now().isoformat()
        ws.append([
            datetime.datetime.now().strftime("%B"), category, subcategory,
            price, datetime.datetime.now().strftime('%d/%m/%Y'), record_timestamp
        ])
        wb.save(LOCAL_EXPENSE_PATH)
        await update.message.reply_text(
            f"<b>Expense saved 📌</b>\n\n<b>Category:</b> {category}\n"
            f"<b>Subcategory:</b> {subcategory}\n<b>Price:</b> {price} €",
            parse_mode='HTML',
            reply_markup=markup
        )
        update_spent(category, price)
        await check_budget(category)
    except ValueError:
        await update.message.reply_text("Please enter a valid price. 🚨",
                                        reply_markup=markup)

    return CHOOSING


async def ask_deleting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to select an expense to delete if any expenses exist.
    """
    if is_local_expense_file_empty():
        await update.message.reply_text(
            "You have not yet registered expenses."
        )
        return CHOOSING

    if 'current_page' not in context.user_data:
        context.user_data['current_page'] = 0

    return await show_expenses(update, context)


async def show_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Display paginated list of expenses for deletion.
    """
    wb, ws = get_local_expense_wb()
    expenses = pd.DataFrame(ws.values)

    if len(expenses.columns) > 0:
        expenses.columns = expenses.iloc[0]
        expenses = expenses[1:]

    num_rows = len(expenses)
    current_page = context.user_data['current_page']

    start_index = max(num_rows - (current_page + 1) * ITEMS_PER_PAGE, 0)
    end_index = min(num_rows - current_page * ITEMS_PER_PAGE, num_rows)

    expense_buttons = []
    for i, (index, row) in enumerate(expenses.iloc[start_index:end_index].iterrows()):
        button_text = f"🗑️ ({row['Date']}) {row['Subcategory']}: {row['Price']} €"
        button = InlineKeyboardButton(
            button_text, callback_data=f"delete_{index}")
        expense_buttons.append([button])

    navigation_buttons = []
    if start_index > 0:
        navigation_buttons.append(InlineKeyboardButton(
            "⬅️ Previous",
            callback_data="previous"))
    if end_index < num_rows:
        navigation_buttons.append(InlineKeyboardButton(
            "➡️ Next",
            callback_data="next"))

    all_buttons = expense_buttons + \
        [navigation_buttons] if navigation_buttons else expense_buttons

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.edit_text(
            "Choose an expense to delete:",
            reply_markup=InlineKeyboardMarkup(all_buttons)
        )
        await update.callback_query.answer()
    elif hasattr(update, 'message'):
        await update.message.reply_text(
            "Choose an expense to delete:",
            reply_markup=InlineKeyboardMarkup(all_buttons)
        )

    return CHOOSING_ITEM_TO_DELETE


async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle pagination and deletion in expense management.
    """
    query_data = update.callback_query.data

    if query_data.startswith("delete_"):
        expense_id = int(query_data.split("_")[1])
        return await delete_expense(update, context, expense_id)
    elif query_data == "previous":
        context.user_data['current_page'] += 1
    elif query_data == "next":
        context.user_data['current_page'] -= 1

    return await show_expenses(update, context)


async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE, expense_id: int) -> int:
    """
    Delete the specified expense from the spreadsheet and reset pagination.
    """
    wb, ws = get_local_expense_wb()
    try:
        ws.delete_rows(expense_id + 1)
        wb.save(LOCAL_EXPENSE_PATH)
        context.user_data['current_page'] = 0
        await update.callback_query.message.edit_text(
            "Expense deleted successfully. ✅")
    except Exception as e:
        await update.callback_query.reply_text(
            f"Error deleting expense: {e}",
            show_alert=True)

    return CHOOSING


async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show budget options: set budget or show budget.
    """
    budget_buttons = [
        ("Set", "set_budget"),
        ("Show", "show_budget")
    ]
    await update.message.reply_text(
        "Choose an action for budget:",
        reply_markup=build_keyboard(budget_buttons))
    return CHOOSING_BUDGET


async def ask_budget_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to select a category for setting a budget.
    """
    await update.callback_query.message.edit_text(
        "Select a category to set a budget:",
        reply_markup=build_keyboard(categories.keys())
    )
    return CHOOSING_BUDGET_CATEGORY


async def ask_budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Store selected category and prompt user to enter the budget amount.
    """
    context.user_data['budget_category'] = update.callback_query.data
    await update.callback_query.message.edit_text(
        "Enter the budget amount for this category:"
    )
    return CHOOSING_BUDGET_AMOUNT


async def save_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save the entered budget for the selected category.
    """
    try:
        budget = float(update.message.text.replace(',', '.'))
        if budget <= 0:
            raise ValueError("Budget must be greater than 0")

        category = context.user_data['budget_category']
        set_budget(category, budget)
        await update.message.reply_text(
            f"Budget set for {category}: {budget} €"
        )
    except ValueError:
        await update.message.reply_text("Please enter a valid budget amount. 🚨")

    return CHOOSING


async def show_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show all budgets and spent amounts for all categories.
    """
    wb, ws = get_local_budget_wb()
    budgets = []

    for row in ws.iter_rows(min_row=2, max_col=3, values_only=True):
        category, budget, spent = row
        budgets.append((category, budget, spent))

    if budgets:
        message = "Here are your budgets:\n\n"
        for category, budget, spent in budgets:
            message += f"<b>Category:</b> {category}\n<b>Budget:</b> {budget} €\n<b>Spent:</b> {spent} €\n\n"
    else:
        message = "No budgets set."

    await update.callback_query.message.reply_text(message, parse_mode='HTML')

    return CHOOSING


async def ask_charts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Display options for generating different expense charts.
    """
    chart_buttons = [
        ("Pie", "chart_yearly"),
        ("Histogram", "chart_monthly"),
        ("Trend", "chart_trend"),
        ("Heatmap", "chart_heatmap")
    ]
    await update.message.reply_text(
        "Select a chart to view:",
        reply_markup=build_keyboard(chart_buttons))

    return CHOOSING_CHART


async def show_yearly_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Generate and display a yearly pie chart of expenses by category.
    """
    if is_local_expense_file_empty():
        await update.callback_query.message.edit_text(
            "You have not yet registered expenses."
        )
        return CHOOSING

    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df['Price'] = df['Price'].astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_pie_chart(df, 'charts/expense_by_category_by_year.png')
    await update.callback_query.message.edit_text(
        "Yay! You graph is ready:"
    )
    await update.callback_query.message.reply_photo(
        open('charts/expense_by_category_by_year.png', 'rb'),
        caption="Expense by category (yearly)"
    )
    return CHOOSING


async def show_trend_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Generate and display a trend chart of the top 3 expense categories by month.
    """
    if is_local_expense_file_empty():
        await update.callback_query.message.edit_text(
            "You have not yet registered expenses."
        )
        return CHOOSING
    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df['Price'] = df['Price'].astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_trend_chart(df, 'charts/expense_trend_top_categories_by_month.png')
    await update.callback_query.message.edit_text(
        "Yay! You graph is ready:"
    )
    await update.callback_query.message.reply_photo(
        open('charts/expense_trend_top_categories_by_month.png', 'rb'),
        caption="Trend top 3 categories (monthly)")

    return CHOOSING


async def show_monthly_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Generate and display a monthly stacked bar chart of expenses by category.
    """
    if is_local_expense_file_empty():
        await update.callback_query.message.edit_text(
            "You have not yet registered expenses."
        )
        return CHOOSING
    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df['Price'] = df['Price'].astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_stacked_bar_chart(df, 'charts/monthly_expenses_by_category.png')
    await update.callback_query.message.edit_text(
        "Yay! You graph is ready:"
    )
    await update.callback_query.message.reply_photo(
        open('charts/heatmap_expense_intensity.png', 'rb'),
        caption="Heatmap of expense intensity (monthly)"
    )

    return CHOOSING


async def show_heatmap_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Generate and display a heatmap of monthly expense intensity.
    """
    if is_local_expense_file_empty():
        await update.callback_query.message.edit_text(
            "You have not yet registered expenses."
        )
        return CHOOSING
    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df['Price'] = df['Price'].astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    await save_heatmap(df, 'charts/heatmap_expense_intensity.png')
    await update.callback_query.message.edit_text(
        "Yay! You graph is ready:"
    )
    await update.callback_query.message.reply_photo(
        open('charts/heatmap_expense_intensity.png', 'rb'),
        caption="Heatmap of expense intensity (monthly)"
    )

    return CHOOSING


async def make_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Generate and send a summary list of expenses for the current year.
    """
    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)

    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]

    df = pd.DataFrame(values, columns=values.columns)
    df['Price'] = df['Price'].astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    current_year = datetime.datetime.now().year
    df_current_year = df[df['Date'].dt.year == current_year]

    message = ""
    grouped = df_current_year.groupby(
        [df_current_year['Date'].dt.month, 'Category'])['Price'].sum()
    total_per_month = df_current_year.groupby(
        df_current_year['Date'].dt.month)['Price'].sum()

    for month in range(1, datetime.datetime.now().month + 1):
        month_name = calendar.month_name[month]
        message += f"\n<b>{month_name}:</b>\n"
        if month in grouped.index.get_level_values(0):
            for category, amount in grouped[month].items():
                message += f"  - {category}: {amount:.2f} €\n"
        total = total_per_month.get(month, 0)
        message += f"  <b>Total:</b> {total:.2f} €\n"
    await update.message.reply_text(message, parse_mode='HTML')

    return CHOOSING


async def ask_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Present the current Google Sheets synchronization status and provide options to enable/disable it.
    """
    settings = load_settings()
    google_sync_status = "enabled" if settings['google_sync']['enabled'] else "disabled"
    google_sync_button_text = "Disable Google Sheet sync" if google_sync_status == "enabled" else "Enable Google Sheet sync"
    google_sync_callback_data = "disable_sync" if google_sync_status == "enabled" else "enable_sync"

    budget_notification_status = "enabled" if settings[
        'budget_notifications']['enabled'] else "disabled"
    budget_notification_button_text = "Disable budget notification" if budget_notification_status == "enabled" else "Enable budget notification"
    budget_notification_callback_data = "disable_budget_notifications" if budget_notification_status == "enabled" else "enable_budget_notifications"

    settings_keyboard = [
        (google_sync_button_text, google_sync_callback_data),
        (budget_notification_button_text, budget_notification_callback_data)
    ]
    message = (f"- Google Sheets sync is currently <u>{google_sync_status}</u>.\n"
               f"- Budget notifications are currently <u>{budget_notification_status}</u>.\n")
    await update.message.reply_text(
        message,
        reply_markup=build_keyboard(settings_keyboard),
        parse_mode='HTML',
    )
    return CHOOSING


async def handle_settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the user's choice to enable or disable Google Sheets synchronization or budget notifications.
    """
    query_data = update.callback_query.data
    settings = load_settings()

    if query_data == "enable_sync":
        settings['google_sync']['enabled'] = True
        message = "Google Sheets synchronization is now enabled (sync happen every 30 minutes)."
    elif query_data == "disable_sync":
        settings['google_sync']['enabled'] = False
        message = "Google Sheets synchronization is now disabled."
    elif query_data == "enable_budget_notifications":
        settings['budget_notifications']['enabled'] = True
        message = "Budget notifications are now enabled (whenever you exceed the budget)."
    elif query_data == "disable_budget_notifications":
        settings['budget_notifications']['enabled'] = False
        message = "Budget notifications are now disabled."

    save_settings(settings)
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(message)

    return CHOOSING


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Clear user data and restart the conversation flow.
    """
    context.user_data.clear()

    return await start(update, context)
