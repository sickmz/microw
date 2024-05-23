from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler
)
from telegram import Update
from handlers import (
    start, ask_category, ask_subcategory, ask_price,
    save_on_local_spreadsheet, ask_deleting, handle_navigation,
    make_charts, make_list, ask_settings,
    handle_settings_choice, invalid_transition, fallback
)
from handlers import (
    show_yearly_chart, show_monthly_chart,
    show_trend_chart, show_heatmap_chart
)
from constants import (
    CHOOSING, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY,
    CHOOSING_PRICE, CHOOSING_ITEM_TO_DELETE, CHOOSING_CHART
)
from config import BOT_TOKEN
from sync import start_scheduler


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
                MessageHandler(filters.Regex("^⚙️ Settings$"), ask_settings),
                CallbackQueryHandler(
                    handle_settings_choice, pattern="^(enable_sync|disable_sync)$"
                ),
            ],
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(ask_subcategory),
                MessageHandler(
                    filters.Regex("^(❌ Delete|📊 Charts|📋 List|⚙️ Settings)$"
                                  ),
                    invalid_transition
                )
            ],
            CHOOSING_SUBCATEGORY: [
                CallbackQueryHandler(ask_price),
                MessageHandler(
                    filters.Regex("^(❌ Delete|📊 Charts|📋 List|⚙️ Settings)$"
                                  ),
                    invalid_transition
                )
            ],
            CHOOSING_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, save_on_local_spreadsheet),
                MessageHandler(
                    filters.Regex("^(❌ Delete|📊 Charts|📋 List|⚙️ Settings)$"
                                  ),
                    invalid_transition
                )
            ],
            CHOOSING_ITEM_TO_DELETE: [
                CallbackQueryHandler(handle_navigation),
                MessageHandler(
                    filters.Regex("^(✏️ Add|📊 Charts|📋 List|⚙️ Settings)$"
                                  ),
                    invalid_transition
                )
            ],
            CHOOSING_CHART: [
                CallbackQueryHandler(
                    show_yearly_chart, pattern="^chart_yearly$"
                ),
                CallbackQueryHandler(
                    show_monthly_chart, pattern="^chart_monthly$"
                ),
                CallbackQueryHandler(
                    show_trend_chart, pattern="^chart_trend$"
                ),
                CallbackQueryHandler(
                    show_heatmap_chart, pattern="^chart_heatmap$"
                ),
                MessageHandler(
                    filters.Regex("^(✏️ Add|❌ Delete|📋 List|⚙️ Settings)$"
                                  ),
                    invalid_transition
                )
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🔄 Reset$"), fallback)
        ],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    scheduler = start_scheduler()
    main()
