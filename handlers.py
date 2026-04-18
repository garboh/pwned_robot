"""
Telegram bot handlers — commands, conversations, payments, and inline buttons.
All user-facing text is loaded from strings.py (IT / EN).
"""

import logging
from html import escape
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction

from config import settings
from database import db_manager
from hibp_client import HibpClient, HibpApiError
from models import User
from scheduler import MAX_MONITORED_PREMIUM
from security import InputValidator, handle_errors, require_admin, AuditLogger
from strings import t, SUBSCRIPTION_PRICE_STARS, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_EMAIL = 1
WAITING_FOR_SCAN_TYPE = 2

HIBP_CHANNEL_URL = "https://t.me/HIBP_updates"
_PREMIUM_RATE_LIMIT = 30


class BotHandlers:
    """Collection of bot command and message handlers."""

    def __init__(self, hibp_client: HibpClient):
        self.hibp_client = hibp_client

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _lang(db_user: Optional[User]) -> str:
        """Return the user's preferred language, defaulting to 'it'."""
        if db_user and db_user.language_code in SUPPORTED_LANGUAGES:
            return db_user.language_code
        return "it"

    # ------------------------------------------------------------------ #
    #  /start                                                              #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = await db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code or "it",
        )
        await db_manager.update_user_activity(db_user.id)
        lang = self._lang(db_user)

        name = f" {escape(user.first_name)}" if user.first_name else ""
        badge = "⭐" if db_user.premium else ""

        keyboard = [
            [
                InlineKeyboardButton(t("btn_check", lang), callback_data="start_check"),
                InlineKeyboardButton(t("btn_stats", lang), callback_data="show_stats"),
            ],
            [
                InlineKeyboardButton(t("btn_premium", lang), callback_data="show_premium"),
                InlineKeyboardButton(t("btn_help", lang), callback_data="show_help"),
            ],
            [InlineKeyboardButton(t("btn_channel", lang), url=HIBP_CHANNEL_URL)],
        ]
        await update.message.reply_html(
            t("welcome", lang, name=name, badge=badge),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # ------------------------------------------------------------------ #
    #  Inline keyboard callbacks                                           #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "start_check":
            db_user = await db_manager.get_user(update.effective_user.id)
            lang = self._lang(db_user)
            await query.message.reply_html(t("check_ask_email", lang))

        elif data == "show_stats":
            await self.stats_command(update, context)

        elif data == "show_help":
            await self.help_command(update, context)

        elif data == "show_premium":
            await self.subscribe_command(update, context)

        elif data == "buy_premium":
            await self._send_invoice(update, context)

        elif data == "lang_it":
            await db_manager.update_user_language(update.effective_user.id, "it")
            await query.message.reply_html(t("language_changed_it", "it"))

        elif data == "lang_en":
            await db_manager.update_user_language(update.effective_user.id, "en")
            await query.message.reply_html(t("language_changed_en", "en"))

    # ------------------------------------------------------------------ #
    #  /help                                                               #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply = (
            update.callback_query.message.reply_html
            if update.callback_query
            else update.message.reply_html
        )
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)
        await reply(t("help", lang), disable_web_page_preview=True)

    # ------------------------------------------------------------------ #
    #  /privacy                                                            #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def privacy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)
        await update.message.reply_html(t("privacy", lang), disable_web_page_preview=True)

    # ------------------------------------------------------------------ #
    #  /language                                                           #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)
        keyboard = [
            [
                InlineKeyboardButton(t("btn_lang_it", lang), callback_data="lang_it"),
                InlineKeyboardButton(t("btn_lang_en", lang), callback_data="lang_en"),
            ]
        ]
        await update.message.reply_html(
            t("language_select", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # ------------------------------------------------------------------ #
    #  /check (conversation)                                               #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args:
            await self._perform_check(update, context, " ".join(context.args))
            return ConversationHandler.END

        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)
        await update.message.reply_html(t("check_ask_email", lang))
        return WAITING_FOR_EMAIL

    @handle_errors
    async def receive_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        email = update.message.text.strip()
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)

        is_valid, sanitized = InputValidator.validate_email(email)
        if not is_valid:
            await update.message.reply_html(t("check_invalid_email", lang))
            return WAITING_FOR_EMAIL

        if InputValidator.check_injection_attempts(email):
            AuditLogger.log_suspicious_activity(
                update.effective_user.id,
                f"Injection attempt: {email}",
                severity="high",
            )
            await update.message.reply_html(t("check_injection", lang))
            return ConversationHandler.END

        await self._perform_check(update, context, sanitized)
        return ConversationHandler.END

    async def _perform_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE, email: str):
        user = update.effective_user
        db_user = await db_manager.get_user(user.id)
        if not db_user:
            await update.message.reply_text(t("user_not_found"))
            return

        lang = self._lang(db_user)
        rate_limit = _PREMIUM_RATE_LIMIT if db_user.premium else settings.MAX_REQUESTS_PER_MINUTE
        is_allowed, _ = await db_manager.check_rate_limit(db_user.id, "check_breach", rate_limit, 60)

        if not is_allowed:
            hint = "" if db_user.premium else t("rate_limit_hint", lang)
            await update.message.reply_html(t("rate_limit", lang) + hint)
            return

        await db_manager.record_request(db_user.id, "check_breach")
        processing = await update.message.reply_html(
            t("check_processing", lang, email=escape(email))
        )
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

        try:
            breaches = (await self.hibp_client.check_breaches(email)).get("data") or []
            pastes   = (await self.hibp_client.check_pastes(email)).get("data") or []

            await db_manager.create_breach_check(
                user_id=db_user.id,
                email=email,
                breaches_found=len(breaches),
                pastes_found=len(pastes),
                check_successful=True,
            )
            AuditLogger.log_breach_check(user_id=db_user.id, email=email, success=True)

            if not breaches and not pastes:
                response = t("check_no_breach", lang, email=escape(email))
            else:
                response = t("check_breach_header", lang, email=escape(email))

                if breaches:
                    response += t("check_breach_count", lang, count=len(breaches))
                    limit = len(breaches) if db_user.premium else 5
                    for breach in breaches[:limit]:
                        name = escape(breach.get("Name", "Unknown"))
                        date = breach.get("BreachDate", "?")
                        if db_user.premium:
                            count = f"{int(breach.get('PwnCount') or 0):,}"
                            classes = ", ".join(breach.get("DataClasses", [])[:5]) or "—"
                            response += t("check_breach_item_premium", lang,
                                          name=name, date=date, count=count, classes=classes)
                        else:
                            response += t("check_breach_item", lang, name=name, date=date)
                    if not db_user.premium and len(breaches) > 5:
                        response += t("check_more_breaches", lang, n=len(breaches) - 5)
                    response += "\n"

                if pastes:
                    response += t("check_pastes_count", lang, count=len(pastes))
                    if db_user.premium:
                        for paste in pastes[:5]:
                            response += t("check_pastes_detail", lang,
                                          source=escape(paste.get("Source", "?")),
                                          title=escape(paste.get("Title") or "—"))
                    else:
                        response += t("check_pastes_hint", lang)
                    response += "\n"

                response += t("check_actions", lang)
                if db_user.premium:
                    response += t("check_monitor_hint", lang)

            try:
                await processing.delete()
            except Exception:
                pass
            await update.message.reply_html(response, disable_web_page_preview=True)

        except HibpApiError as e:
            logger.error("HIBP API error: %s", e)
            await db_manager.create_breach_check(
                user_id=db_user.id, email=email, check_successful=False, error_message=str(e)
            )
            try:
                await processing.delete()
            except Exception:
                pass
            await update.message.reply_html(t("check_api_error", lang))

        except Exception as e:
            logger.error("Unexpected check error: %s", e)
            AuditLogger.log_suspicious_activity(db_user.id, f"Check error: {e}", severity="medium")
            try:
                await processing.delete()
            except Exception:
                pass
            await update.message.reply_text(t("check_generic_error", lang))

    # ------------------------------------------------------------------ #
    #  /stats                                                              #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.callback_query.message if update.callback_query else update.message
        user = update.effective_user
        db_user = await db_manager.get_user(user.id)
        if not db_user:
            await msg.reply_text(t("user_not_found"))
            return

        lang = self._lang(db_user)
        stats = await db_manager.get_user_stats(db_user.id)
        recent = await db_manager.get_user_breach_checks(db_user.id, limit=5)

        text = t("stats_header", lang)
        text += escape(user.first_name or "—")

        if db_user.premium:
            monitored = await db_manager.count_monitored_emails(db_user.id)
            since = db_user.premium_since.strftime("%d/%m/%Y") if db_user.premium_since else "—"
            text += t("stats_premium_line", lang, since=since,
                      monitored=monitored, max=MAX_MONITORED_PREMIUM)
        text += "\n"
        text += t("stats_checks",  lang, total=stats["total_checks"])
        text += t("stats_breaches", lang, total=stats["total_breaches"])
        if stats["total_checks"] > 0:
            text += t("stats_avg", lang, avg=stats["average_breaches"])

        if recent:
            text += t("stats_recent", lang)
            for c in recent:
                icon = "✅" if c.check_successful else "❌"
                breach_info = f" ({c.breaches_found} breach)" if c.breaches_found else ""
                text += t("stats_recent_item", lang,
                           icon=icon,
                           date=c.checked_at.strftime("%d/%m/%Y %H:%M"),
                           breach_info=breach_info)

        if not db_user.premium:
            text += t("stats_subscribe_hint", lang)

        await msg.reply_html(text)

    # ------------------------------------------------------------------ #
    #  /subscribe                                                          #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.callback_query.message if update.callback_query else update.message
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)

        if db_user and db_user.premium:
            text = t("subscribe_already", lang, max=MAX_MONITORED_PREMIUM)
            keyboard = [[InlineKeyboardButton(t("btn_open_channel", lang), url=HIBP_CHANNEL_URL)]]
        else:
            text = t("subscribe_info", lang,
                     max=MAX_MONITORED_PREMIUM, price=SUBSCRIPTION_PRICE_STARS)
            keyboard = [
                [InlineKeyboardButton(t("btn_buy", lang), callback_data="buy_premium")],
                [InlineKeyboardButton(t("btn_open_channel", lang), url=HIBP_CHANNEL_URL)],
            ]

        await msg.reply_html(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )

    # ------------------------------------------------------------------ #
    #  Telegram Stars invoice                                              #
    # ------------------------------------------------------------------ #

    async def _send_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a Telegram Stars invoice for annual Premium."""
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)

        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=t("invoice_title", lang),
            description=t("invoice_description", lang),
            payload="premium_annual_v1",
            provider_token="",   # empty string required for Telegram Stars (XTR)
            currency="XTR",
            prices=[LabeledPrice(t("invoice_label", lang), SUBSCRIPTION_PRICE_STARS)],
        )

    @handle_errors
    async def pre_checkout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Approve all pre-checkout queries with the expected payload."""
        query = update.pre_checkout_query
        if query.invoice_payload == "premium_annual_v1":
            await query.answer(ok=True)
        else:
            await query.answer(ok=False, error_message="Payload non riconosciuto.")

    @handle_errors
    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activate Premium after a successful Stars payment."""
        user = update.effective_user
        db_user = await db_manager.get_user(user.id)
        lang = self._lang(db_user)
        success = await db_manager.set_user_premium(user.id, premium=True)
        if success:
            await update.message.reply_html(t("payment_success", lang))
            logger.info("Premium activated via Stars for user %s", user.id)
        else:
            await update.message.reply_html(t("payment_error", lang))
            logger.error("Failed to activate premium for user %s", user.id)

    # ------------------------------------------------------------------ #
    #  /updates                                                            #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def updates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)
        keyboard = [[InlineKeyboardButton(t("btn_open_channel", lang), url=HIBP_CHANNEL_URL)]]
        await update.message.reply_html(
            t("updates", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )

    # ------------------------------------------------------------------ #
    #  /monitor  (Premium)                                                 #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = await db_manager.get_user(user.id)
        if not db_user:
            await update.message.reply_text(t("user_not_found"))
            return

        lang = self._lang(db_user)

        if not db_user.premium:
            await update.message.reply_html(t("monitor_premium_required", lang))
            return

        if not context.args:
            await update.message.reply_html(t("monitor_usage", lang, max=MAX_MONITORED_PREMIUM))
            return

        is_valid, email = InputValidator.validate_email(context.args[0].strip())
        if not is_valid:
            await update.message.reply_html(t("monitor_invalid_email", lang))
            return

        current = await db_manager.count_monitored_emails(db_user.id)
        if current >= MAX_MONITORED_PREMIUM:
            await update.message.reply_html(t("monitor_limit_reached", lang, max=MAX_MONITORED_PREMIUM))
            return

        processing = await update.message.reply_html(
            t("monitor_processing", lang, email=escape(email))
        )
        try:
            breaches = (await self.hibp_client.check_breaches(email)).get("data") or []
            pastes   = (await self.hibp_client.check_pastes(email)).get("data") or []
        except Exception as e:
            logger.error("Initial monitor check failed: %s", e)
            breaches, pastes = [], []

        try:
            await processing.delete()
        except Exception:
            pass

        result = await db_manager.add_monitored_email(
            user_id=db_user.id,
            email=email,
            initial_breaches=len(breaches),
            initial_pastes=len(pastes),
        )
        if result is None:
            await update.message.reply_html(t("monitor_already", lang, email=escape(email)))
            return

        await update.message.reply_html(
            t("monitor_added", lang,
              email=escape(email),
              breaches=len(breaches),
              pastes=len(pastes),
              used=current + 1,
              max=MAX_MONITORED_PREMIUM)
        )

    # ------------------------------------------------------------------ #
    #  /unmonitor  (Premium)                                               #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def unmonitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = await db_manager.get_user(update.effective_user.id)
        if not db_user:
            await update.message.reply_text(t("user_not_found"))
            return

        lang = self._lang(db_user)
        if not db_user.premium:
            await update.message.reply_html(t("monitor_premium_required", lang))
            return

        if not context.args:
            await update.message.reply_html(t("unmonitor_usage", lang))
            return

        is_valid, email = InputValidator.validate_email(context.args[0].strip())
        if not is_valid:
            await update.message.reply_html(t("check_invalid_email", lang))
            return

        removed = await db_manager.remove_monitored_email(db_user.id, email)
        key = "unmonitor_removed" if removed else "unmonitor_not_found"
        await update.message.reply_html(t(key, lang, email=escape(email)))

    # ------------------------------------------------------------------ #
    #  /mymonitors  (Premium)                                              #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def mymonitors_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = await db_manager.get_user(update.effective_user.id)
        if not db_user:
            await update.message.reply_text(t("user_not_found"))
            return

        lang = self._lang(db_user)
        if not db_user.premium:
            await update.message.reply_html(t("monitor_premium_required", lang))
            return

        monitored = await db_manager.get_monitored_emails(db_user.id)
        if not monitored:
            await update.message.reply_html(t("mymonitors_none", lang))
            return

        text = t("mymonitors_header", lang, count=len(monitored), max=MAX_MONITORED_PREMIUM)
        for m in monitored:
            last = m.last_checked_at.strftime("%d/%m %H:%M") if m.last_checked_at else "—"
            text += t("mymonitors_item", lang,
                      email=escape(m.email),
                      breaches=m.last_breaches_count,
                      pastes=m.last_pastes_count,
                      last=last)
        text += t("mymonitors_hint", lang)
        await update.message.reply_html(text)

    # ------------------------------------------------------------------ #
    #  Admin commands                                                      #
    # ------------------------------------------------------------------ #

    @handle_errors
    @require_admin
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = await db_manager.get_global_stats()
        await update.message.reply_html(
            f"📊 <b>Statistiche globali (Admin)</b>\n\n"
            f"👥 Utenti totali: {stats['total_users']}\n"
            f"📧 Controlli totali: {stats['total_checks']}\n"
            f"📈 Media controlli/utente: {stats['average_checks_per_user']:.2f}\n"
        )

    @handle_errors
    @require_admin
    async def admin_set_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_html(
                "Uso: <code>/setpremium &lt;telegram_id&gt;</code>"
            )
            return
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ ID non valido.")
            return
        success = await db_manager.set_user_premium(target_id, premium=True)
        msg = f"✅ Premium attivato per <code>{target_id}</code>." if success else "❌ Utente non trovato."
        await update.message.reply_html(msg)

    @handle_errors
    @require_admin
    async def admin_revoke_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_html(
                "Uso: <code>/revokepremium &lt;telegram_id&gt;</code>"
            )
            return
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ ID non valido.")
            return
        success = await db_manager.set_user_premium(target_id, premium=False)
        msg = f"✅ Premium revocato per <code>{target_id}</code>." if success else "❌ Utente non trovato."
        await update.message.reply_html(msg)

    # ------------------------------------------------------------------ #
    #  /cancel                                                             #
    # ------------------------------------------------------------------ #

    @handle_errors
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = await db_manager.get_user(update.effective_user.id)
        lang = self._lang(db_user)
        await update.message.reply_text(t("cancel", lang))
        return ConversationHandler.END
