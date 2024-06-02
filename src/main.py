from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import Update

from handlers import start
from handlers import ask_category, ask_subcategory, ask_price, save_on_local_spreadsheet
from handlers import ask_deleting, handle_deletion, handle_pagination
from handlers import ask_charts, make_list
from handlers import ask_settings, handle_settings_choice
from handlers import fallback
from handlers import show_yearly_chart, show_monthly_chart, show_trend_chart, show_heatmap_chart
from handlers import ask_budget, ask_budget_category, ask_budget_amount, show_budget, save_budget

from constants import CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, CHOOSING_PRICE
from constants import CHOOSING_ITEM_TO_DELETE
from constants import CHOOSING_CHART
from constants import CHOOSING_BUDGET, CHOOSING_BUDGET_CATEGORY, CHOOSING_BUDGET_AMOUNT

from config import TELEGRAM_BOT_TOKEN

from sync import start_scheduler

menu_handlers = [
    MessageHandler(filters.Regex("^✏️ Add$"), ask_category),
    MessageHandler(filters.Regex("^❌ Delete$"), ask_deleting),
    MessageHandler(filters.Regex("^📊 Charts$"), ask_charts),
    MessageHandler(filters.Regex("^📋 List$"), make_list),
    MessageHandler(filters.Regex("^💰 Budget$"), ask_budget),
    MessageHandler(filters.Regex("^⚙️ Settings$"), ask_settings),
]


def main() -> None:
    """
    Main function to start the bot.
    Initializes the application, sets up conversation handlers, and starts polling.
    """
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: menu_handlers + [
                MessageHandler(filters.Regex(
                    "^Enable Google Sheet sync$"), handle_settings_choice),
                MessageHandler(filters.Regex(
                    "^Disable Google Sheet sync$"), handle_settings_choice),
                MessageHandler(filters.Regex(
                    "^Enable budget notification$"), handle_settings_choice),
                MessageHandler(filters.Regex(
                    "^Disable budget notification$"), handle_settings_choice),
            ],
            CHOOSING_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_subcategory)],
            CHOOSING_SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_price)],

            CHOOSING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_on_local_spreadsheet)],

            CHOOSING_ITEM_TO_DELETE: [
                MessageHandler(filters.Regex(
                    r"^🔥 \d{2}/\d{2}/\d{4} [\w\s]+/[\w\s]+: (\d+(?:,\d{2})?) €$"), handle_deletion),

                MessageHandler(filters.Regex(
                    "^(⬅️ Previous|➡️ Next)$"), handle_pagination)
            ],
            CHOOSING_CHART: [
                MessageHandler(filters.Regex("^Pie$"), show_yearly_chart),
                MessageHandler(filters.Regex("^Histogram$"),
                               show_monthly_chart),
                MessageHandler(filters.Regex("^Trend$"), show_trend_chart),
                MessageHandler(filters.Regex("^Heatmap$"), show_heatmap_chart),
            ],

            CHOOSING_BUDGET: [
                MessageHandler(filters.Regex("^Set$"), ask_budget_category),
                MessageHandler(filters.Regex("^Show$"), show_budget),
            ],
            CHOOSING_BUDGET_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               ask_budget_amount),
            ],

            CHOOSING_BUDGET_AMOUNT: menu_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_budget)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^/cancel$"), fallback)
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    scheduler = start_scheduler()
    main()
