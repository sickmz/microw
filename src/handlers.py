import calendar
import datetime

import pandas as pd
from config import ITEMS_PER_PAGE, TELEGRAM_USER_ID, logger
from constants import (
    CHOOSING,
    CHOOSING_BUDGET,
    CHOOSING_BUDGET_AMOUNT,
    CHOOSING_BUDGET_CATEGORY,
    CHOOSING_CATEGORY,
    CHOOSING_CHART,
    CHOOSING_ITEM_TO_DELETE,
    CHOOSING_PRICE,
    CHOOSING_SUBCATEGORY,
    LOCAL_EXPENSE_PATH,
    categories,
    markup,
)
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler
from utils import (
    build_keyboard,
    check_budget,
    get_current_budget,
    get_local_budget_wb,
    get_local_expense_wb,
    is_local_expense_file_empty,
    load_settings,
    save_settings,
    set_budget,
    update_spent,
)

from charts import (
    save_heatmap,
    save_pie_chart,
    save_stacked_bar_chart,
    save_trend_chart,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /start command. Verifies user authorization and presents initial menu.
    """
    if str(update.effective_user.id) != str(TELEGRAM_USER_ID):
        await update.message.reply_text("You're not authorized. ⛔")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        "Hi! I'm microw. What can I do for you?", reply_markup=markup
    )
    return CHOOSING


async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to select an expense category using a markup keyboard.
    Uses a dynamic layout for multiple buttons per row.
    """
    category_keys = list(categories.keys())
    reply_markup = build_keyboard(category_keys, buttons_per_row=3)
    await update.message.reply_text("Select a category:", reply_markup=reply_markup)

    return CHOOSING_CATEGORY


async def ask_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Store selected category from the markup keyboard and prompt user to select a subcategory.
    Uses a dynamic layout for multiple buttons per row.
    """
    selected_category = update.message.text
    if selected_category not in categories:
        return await handle_unexpected_message(update, context)

    context.user_data["selected_category"] = selected_category
    subcategory_keys = categories[selected_category]
    reply_markup = build_keyboard(subcategory_keys, buttons_per_row=3)
    await update.message.reply_text("Select a subcategory:", reply_markup=reply_markup)

    return CHOOSING_SUBCATEGORY


async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Store selected subcategory and prompt user to enter the price.
    """
    selected_subcategory = update.message.text
    selected_category = context.user_data.get("selected_category")

    if selected_category and selected_subcategory not in categories.get(
        selected_category, []
    ):
        return await handle_unexpected_message(update, context)

    context.user_data["selected_subcategory"] = selected_subcategory
    logger.info(f"Selected subcategory: {context.user_data['selected_subcategory']}")

    await update.message.reply_text("Enter the price for this item:")
    return CHOOSING_PRICE


async def save_on_local_spreadsheet(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Save the entered expense to the local spreadsheet and provide user feedback.
    """
    try:
        price = float(update.message.text.replace(",", "."))
        category = context.user_data["selected_category"]
        subcategory = context.user_data["selected_subcategory"]

        wb, ws = get_local_expense_wb()
        record_timestamp = datetime.datetime.now().isoformat()
        ws.append(
            [
                datetime.datetime.now().strftime("%B"),
                category,
                subcategory,
                price,
                datetime.datetime.now().strftime("%d/%m/%Y"),
                record_timestamp,
            ]
        )
        wb.save(LOCAL_EXPENSE_PATH)
        await update.message.reply_text(
            f"<b>Expense saved 📌</b>\n\n<b>Category:</b> {category}\n"
            f"<b>Subcategory:</b> {subcategory}\n<b>Price:</b> {price} €",
            parse_mode="HTML",
            reply_markup=markup,
        )
        update_spent(category, price)
        await check_budget(category)
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid price. 🚨", reply_markup=markup
        )

    return CHOOSING


async def ask_deleting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to select an expense to delete if any expenses exist.
    """
    if is_local_expense_file_empty():
        await update.message.reply_text(
            "You have not yet registered expenses.", reply_markup=markup
        )
        return CHOOSING

    if "current_page" not in context.user_data:
        context.user_data["current_page"] = 0

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
    current_page = context.user_data["current_page"]

    start_index = max(num_rows - (current_page + 1) * ITEMS_PER_PAGE, 0)
    end_index = min(num_rows - current_page * ITEMS_PER_PAGE, num_rows)

    expense_buttons = []
    expense_dict = {}

    for i, (index, row) in enumerate(expenses.iloc[start_index:end_index].iterrows()):
        button_text = (
            f"🔥 {row['Date']} {row['Category']}/{row['Subcategory']}: {row['Price']} €"
        )
        expense_buttons.append([KeyboardButton(button_text)])
        expense_dict[button_text] = index

    context.user_data["expense_dict"] = expense_dict

    navigation_buttons = []
    if start_index > 0:
        navigation_buttons.append(KeyboardButton("⬅️ Previous"))
    if end_index < num_rows:
        navigation_buttons.append(KeyboardButton("➡️ Next"))

    if navigation_buttons:
        # Add navigation buttons as a single row
        expense_buttons.append(navigation_buttons)

    reply_markup = ReplyKeyboardMarkup(
        expense_buttons, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Choose an expense to delete:", reply_markup=reply_markup
    )

    return CHOOSING_ITEM_TO_DELETE


async def handle_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    expense_dict = context.user_data.get("expense_dict", {})
    ui_expense_id = expense_dict.get(text)
    if ui_expense_id is None:
        await update.message.reply_text(
            "Invalid selection. Please try again.", reply_markup=markup
        )

        return CHOOSING

    current_page = context.user_data.get("current_page", 0)
    actual_expense_id = ui_expense_id + (current_page * ITEMS_PER_PAGE) + 1

    await delete_expense(update, context, actual_expense_id)

    return CHOOSING


async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle pagination requests.
    """
    text = update.message.text
    if text == "⬅️ Previous":
        context.user_data["current_page"] += 1
    elif text == "➡️ Next":
        context.user_data["current_page"] -= 1

    return await show_expenses(update, context)


async def delete_expense(
    update: Update, context: ContextTypes.DEFAULT_TYPE, expense_id: int
) -> int:
    wb, ws = get_local_expense_wb()
    try:
        ws.delete_rows(expense_id)
        wb.save(LOCAL_EXPENSE_PATH)
        await update.message.reply_text(
            "Expense deleted successfully. ✅", reply_markup=markup
        )
    except Exception as e:
        await update.message.reply_text(
            f"Error deleting expense: {e}", reply_markup=markup
        )
        logger.error(f"Error: {e}")

    return CHOOSING


async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show budget options: set budget or show budget.
    """
    budget_options = ["Set", "Show"]
    reply_markup = build_keyboard(budget_options, buttons_per_row=2)
    await update.message.reply_text(
        "Choose an action for budget:", reply_markup=reply_markup
    )
    return CHOOSING_BUDGET


async def ask_budget_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Prompt user to select a category for setting a budget.
    """
    category_keys = list(categories.keys())
    reply_markup = build_keyboard(category_keys, buttons_per_row=3)
    await update.message.reply_text(
        "Select a category to set a budget:", reply_markup=reply_markup
    )
    return CHOOSING_BUDGET_CATEGORY


async def ask_budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Store the selected budget category and prompt the user to enter the budget amount.
    """
    selected_category = update.message.text
    context.user_data["budget_category"] = selected_category

    if selected_category not in categories:
        return await handle_unexpected_message(update, context)

    current_budget = get_current_budget(selected_category)

    await update.message.reply_text(
        f"Enter the budget amount for {selected_category}. \n(Current budget: {current_budget} €)"
    )
    return CHOOSING_BUDGET_AMOUNT


async def save_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save the entered budget for the selected category.
    """
    try:
        budget = float(update.message.text.replace(",", "."))
        if budget <= 0:
            raise ValueError("Budget must be greater than 0")

        category = context.user_data["budget_category"]
        set_budget(category, budget)
        await update.message.reply_text(
            f"Budget set for {category}: {budget} €", reply_markup=markup
        )
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid budget amount. 🚨", reply_markup=markup
        )

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

    await update.message.reply_text(message, parse_mode="HTML", reply_markup=markup)

    return CHOOSING


async def ask_charts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Display options for generating different expense charts.
    """
    chart_options = ["Pie", "Histogram", "Trend", "Heatmap"]
    reply_markup = build_keyboard(chart_options, buttons_per_row=2)
    await update.message.reply_text(
        "Select a chart to view:", reply_markup=reply_markup
    )
    return CHOOSING_CHART


async def show_yearly_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if is_local_expense_file_empty():
        await update.message.reply_text(
            "You have not yet registered expenses.", reply_markup=markup
        )
        return CHOOSING

    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df["Price"] = df["Price"].astype(float)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    await save_pie_chart(df, "charts/expense_by_category_by_year.png")
    await update.message.reply_text("Yay! Your yearly chart is ready:")
    await update.message.reply_photo(
        open("charts/expense_by_category_by_year.png", "rb"),
        caption="Expense by category (yearly)",
        reply_markup=markup,
    )
    return CHOOSING


async def show_trend_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if is_local_expense_file_empty():
        await update.message.reply_text("You have not yet registered expenses.")
        return CHOOSING

    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df["Price"] = df["Price"].astype(float)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    await save_trend_chart(df, "charts/expense_trend_top_categories_by_month.png")
    await update.message.reply_text("Yay! Your trend chart is ready:")
    await update.message.reply_photo(
        open("charts/expense_trend_top_categories_by_month.png", "rb"),
        caption="Trend top 3 categories (monthly)",
        reply_markup=markup,
    )
    return CHOOSING


async def show_monthly_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if is_local_expense_file_empty():
        await update.message.reply_text("You have not yet registered expenses.")
        return CHOOSING

    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df["Price"] = df["Price"].astype(float)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    await save_stacked_bar_chart(df, "charts/monthly_expenses_by_category.png")
    await update.message.reply_text("Yay! Your monthly chart is ready:")
    await update.message.reply_photo(
        open("charts/monthly_expenses_by_category.png", "rb"),
        caption="Expense by category (monthly)",
        reply_markup=markup,
    )
    return CHOOSING


async def show_heatmap_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if is_local_expense_file_empty():
        await update.message.reply_text("You have not yet registered expenses.")
        return CHOOSING

    wb, ws = get_local_expense_wb()
    values = pd.DataFrame(ws.values)
    if len(values.columns) > 0:
        values.columns = values.iloc[0]
        values = values[1:]
    df = pd.DataFrame(values, columns=values.columns)
    df["Price"] = df["Price"].astype(float)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    await save_heatmap(df, "charts/heatmap_expense_intensity.png")
    await update.message.reply_text("Yay! Your heatmap is ready:")
    await update.message.reply_photo(
        open("charts/heatmap_expense_intensity.png", "rb"),
        caption="Heatmap of expense intensity (monthly)",
        reply_markup=markup,
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
    df["Price"] = df["Price"].astype(float)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    current_year = datetime.datetime.now().year
    df_current_year = df[df["Date"].dt.year == current_year]

    message = ""
    grouped = df_current_year.groupby([df_current_year["Date"].dt.month, "Category"])[
        "Price"
    ].sum()
    total_per_month = df_current_year.groupby(df_current_year["Date"].dt.month)[
        "Price"
    ].sum()

    for month in range(1, datetime.datetime.now().month + 1):
        month_name = calendar.month_name[month]
        message += f"\n<b>{month_name}:</b>\n"
        if month in grouped.index.get_level_values(0):
            for category, amount in grouped[month].items():
                message += f"  - {category}: {amount:.2f} €\n"
        total = total_per_month.get(month, 0)
        message += f"  <b>Total:</b> {total:.2f} €\n"
    await update.message.reply_text(message, parse_mode="HTML")

    return CHOOSING


async def ask_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Present the current Google Sheets synchronization status and provide options to enable/disable it.
    """
    settings = load_settings()
    google_sync_status = "enabled" if settings["google_sync"]["enabled"] else "disabled"
    google_sync_button_text = (
        "Disable Google Sheet sync"
        if google_sync_status == "enabled"
        else "Enable Google Sheet sync"
    )
    budget_notification_status = (
        "enabled" if settings["budget_notifications"]["enabled"] else "disabled"
    )
    budget_notification_button_text = (
        "Disable budget notification"
        if budget_notification_status == "enabled"
        else "Enable budget notification"
    )

    settings_options = [google_sync_button_text, budget_notification_button_text]
    reply_markup = build_keyboard(settings_options, buttons_per_row=2)
    message = (
        f"- Google Sheets sync is currently <u>{google_sync_status}</u>.\n"
        f"- Budget notifications are currently <u>{budget_notification_status}</u>.\n"
    )
    await update.message.reply_text(
        message, reply_markup=reply_markup, parse_mode="HTML"
    )
    return CHOOSING


async def handle_settings_choice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = update.message.text
    settings = load_settings()

    if "Enable Google Sheet sync" in text:
        settings["google_sync"]["enabled"] = True
        message = "Google Sheets synchronization is now enabled."
    elif "Disable Google Sheet sync" in text:
        settings["google_sync"]["enabled"] = False
        message = "Google Sheets synchronization is now disabled."
    elif "Enable budget notification" in text:
        settings["budget_notifications"]["enabled"] = True
        message = "Budget notifications are now enabled."
    elif "Disable budget notification" in text:
        settings["budget_notifications"]["enabled"] = False
        message = "Budget notifications are now disabled."

    save_settings(settings)
    await update.message.reply_text(message, reply_markup=markup)
    return CHOOSING


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Clear user data and restart the conversation flow.
    """
    context.user_data.clear()

    return await start(update, context)


async def handle_unexpected_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text("Huh?", reply_markup=markup)
    return CHOOSING
