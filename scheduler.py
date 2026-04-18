"""
Scheduler jobs for Pwned Robot.
Handles daily breach monitoring for premium subscribers.
"""

import asyncio
import logging
from html import escape

from telegram.ext import ContextTypes

from database import db_manager
from hibp_client import HibpClient, HibpApiError
from strings import t

logger = logging.getLogger(__name__)

# Max emails a premium user can monitor
MAX_MONITORED_PREMIUM = 5

# Seconds between HIBP requests to respect rate limits
_REQUEST_DELAY = 1.5


def _lang(language_code: str) -> str:
    """Normalise language code to a supported value."""
    return language_code if language_code in ("it", "en") else "it"


async def daily_monitoring_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Scheduled daily job: check monitored emails for all premium users and
    send a Telegram notification when new breaches or pastes are detected.

    Registered in main.py via application.job_queue.run_daily().
    The HibpClient instance is retrieved from context.application.bot_data.
    """
    hibp_client: HibpClient = context.application.bot_data.get("hibp_client")
    if hibp_client is None:
        logger.error("daily_monitoring_job: hibp_client not found in bot_data")
        return

    logger.info("Daily breach monitoring started")
    monitored_items = await db_manager.get_all_premium_monitored_emails()

    checked = 0
    notified = 0

    for monitored, user in monitored_items:
        lang = _lang(user.language_code or "it")
        try:
            breaches = (await hibp_client.check_breaches(monitored.email)).get("data") or []
            pastes   = (await hibp_client.check_pastes(monitored.email)).get("data") or []

            new_breaches = len(breaches)
            new_pastes   = len(pastes)

            if (new_breaches > monitored.last_breaches_count or
                    new_pastes > monitored.last_pastes_count):

                added_breaches = new_breaches - monitored.last_breaches_count
                added_pastes   = new_pastes   - monitored.last_pastes_count

                msg = t("alert_header", lang, email=escape(monitored.email))

                if added_breaches > 0:
                    msg += t("alert_breaches", lang, count=added_breaches)
                    for breach in breaches[monitored.last_breaches_count:]:
                        name    = escape(breach.get("Name", "Unknown"))
                        date    = breach.get("BreachDate", "?")
                        records = f"{int(breach.get('PwnCount') or 0):,}"
                        msg += t("alert_breach_item", lang,
                                 name=name, date=date, records=records)
                    msg += "\n"

                if added_pastes > 0:
                    msg += t("alert_pastes", lang, count=added_pastes)

                msg += t("alert_actions", lang)

                try:
                    await context.bot.send_message(
                        chat_id=user.telegram_id,
                        text=msg,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                    notified += 1
                except Exception as send_err:
                    logger.warning(
                        "Failed to notify user %s: %s", user.telegram_id, send_err
                    )

            await db_manager.update_monitored_email_stats(
                monitored.id, new_breaches, new_pastes
            )
            checked += 1

        except HibpApiError as api_err:
            logger.error("HIBP API error for %s: %s", monitored.email, api_err)
        except Exception as err:
            logger.error(
                "Error monitoring %s for user %s: %s",
                monitored.email, user.telegram_id, err,
            )

        await asyncio.sleep(_REQUEST_DELAY)

    logger.info(
        "Daily monitoring complete: %d checked, %d notifications sent",
        checked, notified,
    )
