from config import TELEGRAM_BOT_TOKEN
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
)
from handlers import (
    ask_budget,
    ask_budget_amount,
    ask_budget_category,
    ask_category,
    ask_charts,
    ask_deleting,
    ask_price,
    ask_settings,
    ask_subcategory,
    fallback,
    handle_deletion,
    handle_pagination,
    handle_settings_choice,
    handle_unexpected_message,
    make_list,
    save_budget,
    save_on_local_spreadsheet,
    show_budget,
    show_heatmap_chart,
    show_monthly_chart,
    show_trend_chart,
    show_yearly_chart,
    start,
)
from sync import start_scheduler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)


def main() -> None:
    """
    Main function to start the bot.
    Initializes the application, sets up conversation handlers, and starts polling.
    """
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^✏️ Add$"), ask_category),
                MessageHandler(filters.Regex("^❌ Delete$"), ask_deleting),
                MessageHandler(filters.Regex("^📊 Charts$"), ask_charts),
                MessageHandler(filters.Regex("^📋 List$"), make_list),
                MessageHandler(filters.Regex("^💰 Budget$"), ask_budget),
                MessageHandler(filters.Regex("^⚙️ Settings$"), ask_settings),
                MessageHandler(
                    filters.Regex("^Enable Google Sheet sync$"), handle_settings_choice
                ),
                MessageHandler(
                    filters.Regex("^Disable Google Sheet sync$"), handle_settings_choice
                ),
                MessageHandler(
                    filters.Regex("^Enable budget notification$"),
                    handle_settings_choice,
                ),
                MessageHandler(
                    filters.Regex("^Disable budget notification$"),
                    handle_settings_choice,
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_unexpected_message
                ),
            ],
            CHOOSING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_subcategory),
            ],
            CHOOSING_SUBCATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_price),
            ],
            CHOOSING_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, save_on_local_spreadsheet
                )
            ],
            CHOOSING_ITEM_TO_DELETE: [
                MessageHandler(
                    filters.Regex(
                        r"^🔥 \d{2}/\d{2}/\d{4} [\w\s]+/[\w\s]+: (\d+(?:,\d{2})?) €$"
                    ),
                    handle_deletion,
                ),
                MessageHandler(
                    filters.Regex("^(⬅️ Previous|➡️ Next)$"), handle_pagination
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_unexpected_message
                ),
            ],
            CHOOSING_CHART: [
                MessageHandler(filters.Regex("^Pie$"), show_yearly_chart),
                MessageHandler(filters.Regex("^Histogram$"), show_monthly_chart),
                MessageHandler(filters.Regex("^Trend$"), show_trend_chart),
                MessageHandler(filters.Regex("^Heatmap$"), show_heatmap_chart),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_unexpected_message
                ),
            ],
            CHOOSING_BUDGET: [
                MessageHandler(filters.Regex("^Set$"), ask_budget_category),
                MessageHandler(filters.Regex("^Show$"), show_budget),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_unexpected_message
                ),
            ],
            CHOOSING_BUDGET_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget_amount),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_unexpected_message
                ),
            ],
            CHOOSING_BUDGET_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_budget)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^/cancel$"), fallback)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    scheduler = start_scheduler()
    main()
