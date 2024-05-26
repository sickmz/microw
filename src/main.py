from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import Update

from handlers import start
from handlers import ask_category, ask_subcategory, ask_price, save_on_local_spreadsheet
from handlers import ask_deleting, handle_navigation
from handlers import ask_charts, make_list
from handlers import ask_settings, handle_settings_choice
from handlers import invalid_transition, fallback
from handlers import show_yearly_chart, show_monthly_chart, show_trend_chart, show_heatmap_chart
from handlers import ask_budget, ask_budget_category, ask_budget_amount, show_budget, save_budget

from constants import CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, CHOOSING_PRICE
from constants import CHOOSING_ITEM_TO_DELETE
from constants import CHOOSING_CHART
from constants import CHOOSING_BUDGET, CHOOSING_BUDGET_CATEGORY, CHOOSING_BUDGET_AMOUNT

from config import TELEGRAM_BOT_TOKEN

from sync import start_scheduler


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
                CallbackQueryHandler(handle_settings_choice, pattern="^(enable_sync|disable_sync|enable_budget_notifications|disable_budget_notifications)$")
            ],
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(ask_subcategory),
                MessageHandler(
                    filters.Regex("^(❌ Delete|📊 Charts|📋 List|⚙️ Settings)$"), invalid_transition)
            ],
            CHOOSING_SUBCATEGORY: [
                CallbackQueryHandler(ask_price),
                MessageHandler(filters.Regex("^(❌ Delete|📊 Charts|📋 List|⚙️ Settings)$"), invalid_transition)
            ],
            CHOOSING_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_on_local_spreadsheet), 
                MessageHandler(filters.Regex("^(❌ Delete|📊 Charts|📋 List|⚙️ Settings)$"), invalid_transition)
            ],
            CHOOSING_ITEM_TO_DELETE: [
                CallbackQueryHandler(handle_navigation),
                MessageHandler(filters.Regex("^(✏️ Add|📊 Charts|📋 List|⚙️ Settings)$"), invalid_transition)
            ],
            CHOOSING_CHART: [
                CallbackQueryHandler(show_yearly_chart, pattern="^chart_yearly$"),
                CallbackQueryHandler(show_monthly_chart, pattern="^chart_monthly$"),
                CallbackQueryHandler(show_trend_chart, pattern="^chart_trend$"),
                CallbackQueryHandler(show_heatmap_chart, pattern="^chart_heatmap$"),
                MessageHandler(filters.Regex("^(✏️ Add|❌ Delete|📋 List|⚙️ Settings)$"), invalid_transition)
            ],
            CHOOSING_BUDGET: [
                CallbackQueryHandler(ask_budget_category,pattern="^set_budget$"),
                CallbackQueryHandler(show_budget, pattern="^show_budget$")
            ],
            CHOOSING_BUDGET_CATEGORY: [
                CallbackQueryHandler(ask_budget_amount),
            ],
            CHOOSING_BUDGET_AMOUNT: [
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
