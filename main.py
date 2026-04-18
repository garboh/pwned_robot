"""
Main Telegram bot application with modern async patterns.
Handles bot initialization, handler registration, and graceful shutdown.
"""

import datetime
import logging
import logging.handlers
import sys

from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from config import settings
from database import db_manager
from hibp_client import HibpClient
from handlers import BotHandlers, WAITING_FOR_EMAIL
from scheduler import daily_monitoring_job
from security import AuditLogger

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging with file rotation."""
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(filename)s:%(lineno)d] - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    file_handler = logging.handlers.RotatingFileHandler(
        "pwned_robot.log", maxBytes=10_485_760, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger.info("Logging configured")


async def post_init(application: Application) -> None:
    """Initialize resources after bot starts."""
    logger.info("Starting bot post-initialization...")

    await db_manager.initialize()

    bot_info = await application.bot.get_me()
    logger.info("Bot started: @%s (ID: %s)", bot_info.username, bot_info.id)

    commands = [
        BotCommand("start",        "🚀 Avvia il bot"),
        BotCommand("check",        "🔍 Controlla un'email"),
        BotCommand("stats",        "📊 Le tue statistiche"),
        BotCommand("monitor",      "🔔 Monitoraggio giornaliero (Premium)"),
        BotCommand("unmonitor",    "🗑️ Rimuovi email dal monitoraggio"),
        BotCommand("mymonitors",   "📋 Email monitorate"),
        BotCommand("updates",      "📢 Notizie sulle violazioni"),
        BotCommand("subscribe",    "⭐ Abbonamento Premium"),
        BotCommand("language",     "🌐 Cambia lingua"),
        BotCommand("help",         "❓ Aiuto e informazioni"),
        BotCommand("privacy",      "🔐 Privacy"),
        BotCommand("cancel",       "❌ Annulla operazione"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set: %d commands", len(commands))

    # Schedule daily breach monitoring at 08:00 UTC
    application.job_queue.run_daily(
        daily_monitoring_job,
        time=datetime.time(hour=8, minute=0, tzinfo=datetime.timezone.utc),
        name="daily_breach_monitoring",
    )
    logger.info("Daily monitoring job scheduled at 08:00 UTC")


async def post_stop(application: Application) -> None:
    """Cleanup resources before bot stops."""
    logger.info("Stopping bot...")
    await db_manager.close()
    logger.info("Bot stopped gracefully")


def create_app() -> Application:
    """Create and configure the Telegram bot application."""
    logger.info("Creating bot application...")

    application = (
        Application.builder()
        .token(settings.TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_pool_timeout(30)
        .build()
    )

    hibp_client = HibpClient(settings.HIBP_API_KEY)
    h = BotHandlers(hibp_client)

    # Make hibp_client accessible to scheduled jobs
    application.bot_data["hibp_client"] = hibp_client

    application.post_init = post_init
    application.post_stop = post_stop

    # Global error handler
    async def error_handler(update, context):
        logger.error("Update %s caused error: %s", update, context.error, exc_info=context.error)
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Si è verificato un errore. Per favore, riprova più tardi."
            )
        if update and update.effective_user:
            await AuditLogger.log_security_event(
                update.effective_user.id, "bot_error", str(context.error)
            )

    application.add_error_handler(error_handler)

    # ── /check conversation ──────────────────────────────────────────── #
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("check", h.check_command)],
        states={
            WAITING_FOR_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.receive_email)
            ],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True,
    ))

    # ── Payments ─────────────────────────────────────────────────────── #
    application.add_handler(PreCheckoutQueryHandler(h.pre_checkout_callback))
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, h.successful_payment_callback)
    )

    # ── Inline keyboard callbacks ─────────────────────────────────────── #
    application.add_handler(CallbackQueryHandler(h.button_callback))

    # ── Public commands ───────────────────────────────────────────────── #
    application.add_handler(CommandHandler("start",     h.start))
    application.add_handler(CommandHandler("help",      h.help_command))
    application.add_handler(CommandHandler("privacy",   h.privacy_command))
    application.add_handler(CommandHandler("language",  h.language_command))
    application.add_handler(CommandHandler("stats",     h.stats_command))
    application.add_handler(CommandHandler("subscribe", h.subscribe_command))
    application.add_handler(CommandHandler("updates",   h.updates_command))

    # ── Premium commands ──────────────────────────────────────────────── #
    application.add_handler(CommandHandler("monitor",    h.monitor_command))
    application.add_handler(CommandHandler("unmonitor",  h.unmonitor_command))
    application.add_handler(CommandHandler("mymonitors", h.mymonitors_command))

    # ── Admin commands ────────────────────────────────────────────────── #
    application.add_handler(CommandHandler("adminstats",    h.admin_stats))
    application.add_handler(CommandHandler("setpremium",    h.admin_set_premium))
    application.add_handler(CommandHandler("revokepremium", h.admin_revoke_premium))

    logger.info("Bot handlers registered successfully")
    return application


def main():
    """Main entry point for the bot."""
    setup_logging()

    try:
        logger.info("Starting Pwned Robot v2.0 (Debug: %s)", settings.DEBUG)
        app = create_app()

        if settings.WEBHOOK_URL:
            logger.info("Starting with webhook: %s", settings.WEBHOOK_URL)
            app.run_webhook(
                listen="0.0.0.0",
                port=settings.WEBHOOK_PORT,
                url_path=settings.TELEGRAM_TOKEN,
                webhook_url=f"{settings.WEBHOOK_URL}/{settings.TELEGRAM_TOKEN}",
            )
        else:
            logger.info("Starting with long-polling")
            app.run_polling(
                poll_interval=1.0,
                allowed_updates=[
                    "message",
                    "callback_query",
                    "pre_checkout_query",
                    "my_chat_member",
                ],
            )

    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error("Critical error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
