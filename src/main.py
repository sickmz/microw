from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import Update

from handlers import start
from handlers import ask_category, ask_subcategory, ask_price, save_on_local_spreadsheet
from handlers import ask_deleting, handle_navigation
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
                CallbackQueryHandler(handle_settings_choice, pattern="^(enable_sync|disable_sync|enable_budget_notifications|disable_budget_notifications)$")
            ],
            CHOOSING_CATEGORY: menu_handlers + [
                CallbackQueryHandler(ask_subcategory),
            ],
            CHOOSING_SUBCATEGORY: menu_handlers + [
                CallbackQueryHandler(ask_price),
            ],
            CHOOSING_PRICE: menu_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_on_local_spreadsheet), 
            ],
            CHOOSING_ITEM_TO_DELETE: menu_handlers + [
                CallbackQueryHandler(handle_navigation),
            ],
            CHOOSING_CHART: menu_handlers + [
                CallbackQueryHandler(show_yearly_chart, pattern="^chart_yearly$"),
                CallbackQueryHandler(show_monthly_chart, pattern="^chart_monthly$"),
                CallbackQueryHandler(show_trend_chart, pattern="^chart_trend$"),
                CallbackQueryHandler(show_heatmap_chart, pattern="^chart_heatmap$"),
            ],
            CHOOSING_BUDGET: menu_handlers + [
                CallbackQueryHandler(ask_budget_category,pattern="^set_budget$"),
                CallbackQueryHandler(show_budget, pattern="^show_budget$")
            ],
            CHOOSING_BUDGET_CATEGORY: menu_handlers + [
                CallbackQueryHandler(ask_budget_amount),
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
