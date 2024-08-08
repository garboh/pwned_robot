import logging
import json
import requests
import hashlib
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    PreCheckoutQueryHandler)
from bot import utils, sql_queries
from bot.config import TOKEN, HIBP_API_KEY, PAYMENT_TOKEN
from gettext import translation


# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Translation
en = translation('pwned_robot', localedir='locale', languages=['en'])
_ = en.gettext

# Define error handler
async def error(update: Update, context: CallbackContext):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=_("❌ An error has occurred. Try later."))

# Define command handlers
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if await init(update, context):
        get_service_enabled = utils.get_user_service(chat_id)
        if get_service_enabled == 0:
            str_service_enabled = "Breaches"
        elif get_service_enabled == 1:
            str_service_enabled = "Pastes"
        else:
            str_service_enabled = "Password"
        keyboard_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("📖 Guide"), callback_data="guide"), InlineKeyboardButton(_("ℹ️ Various info"), callback_data="info")],
            [InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text=_("Welcome back {userName}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\nhttps://haveibeenpwned.com\n\nActual service: {str_service_enabled}\n👷‍♂️ You can change the service on the settings").format(userName=update.message.from_user.first_name, str_service_enabled=str_service_enabled),
            reply_markup=keyboard_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

async def feedback(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    utils.set_user_status('feedback', chat_id)
    await update.message.reply_text("Please provide your feedback or type /cancel to cancel.")

async def cancel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_status = utils.get_user_status(chat_id)
    if user_status == 'feedback':
        utils.set_user_status('cancel', chat_id)
        await update.message.reply_text("Feedback canceled.", reply_markup=ReplyKeyboardRemove())
    elif user_status == 'donate':
        utils.set_user_status('cancel', chat_id)
        await update.message.reply_text("Action donate canceled.", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("No action to cancel.", reply_markup=ReplyKeyboardRemove())

async def testo(update: Update, context: CallbackContext):
    if await init(update, context):
        await check_pwned(update, context, update.message.chat_id, update.message.text, 1)

async def check_pwned(update: Update, context: CallbackContext, chat_id, message, offset=1):
    chat_id = chat_id
    msg = message

    # Filtra i comandi del bot
    if msg.startswith('/'):
        return
    
    offset = offset
    service = utils.get_user_service(chat_id)
    normal = True
    truncate = ""
    cache = ""
    
    if service == 0:
        actualService = "breachedaccount"
        truncate = "?truncateResponse=false"
        cache = "breached"
    elif service == 1:
        actualService = "pasteaccount"
        cache = "paste"
    elif service == 2:
        count = safepass(msg)
        if count == 0:
            await context.bot.send_message(
                chat_id=chat_id,
                text=_("<b>Good news — no pwnage found!</b>\n\nThis password wasn't found in any of the Pwned Passwords loaded into Have I Been Pwned. That doesn't necessarily mean it's a good password, merely that it's not indexed on this site."),
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=_("<b>Oh no — pwned!</b>\n\nThis password has been seen {} times before.\nThis password has previously appeared in a data breach and should never be used. If you've ever used it anywhere before, change it!").format(count),
                parse_mode=ParseMode.HTML
            )
        normal = False

    if normal:
        customheaders = {
            'User-Agent': 'Pwnage-Checker-For-Telegram',
            'api-version': '3',
            'Accept': 'application/vnd.haveibeenpwned.v3+json',
            'hibp-api-key': HIBP_API_KEY
        }
        url = f"https://haveibeenpwned.com/api/v3/{actualService}/{urllib.parse.quote_plus(msg)}{truncate}"
        r = requests.get(url, headers=customheaders)

        if r.status_code == 200:
            json_object = r.json()
            with open(f'./cache/{cache}/{chat_id}.json', 'w', encoding='utf-8') as f:
                json.dump(json_object, f, ensure_ascii=False, indent=4)

            stringAnsw = ""
            countRow = 0
            countRowIn = 0

            for row in json_object:
                countRow += 1

            for rows in json_object:
                countRowIn += 1
                if countRowIn == offset:
                    if service == 0:
                        if rows.get("LogoPath"):
                            stringAnsw += f"<a href='{rows['LogoPath']}'>🔴</a> Page: {offset} / {countRow} Breach found \n"
                        else:
                            stringAnsw += f"🔴 Page: {offset} / {countRow} Breach found \n"
                        if rows.get("IsVerified"):
                            if rows['IsVerified']:
                                stringAnsw += "\n✅ Breach verified"
                            else:
                                stringAnsw += "\n🚫 Breach not verified"
                        if rows.get("Name"):
                            stringAnsw += f"\nℹ️ {rows['Name']}"
                        if rows.get("Title"):
                            stringAnsw += f"\n🔤 {rows['Title']}"
                        if rows.get("Domain"):
                            stringAnsw += f"\n🌐 {rows['Domain']}"
                        if rows.get("BreachDate"):
                            stringAnsw += f"\n📅 Breach Date: {rows['BreachDate']}"
                        if rows.get("AddedDate"):
                            stringAnsw += f"\n➕ Added on: {rows['AddedDate']}"
                        if rows.get("ModifiedDate"):
                            stringAnsw += f"\n📆 Modified on: {rows['ModifiedDate']}"
                        if rows.get("DataClasses"):
                            stringAnsw += "\n📚 Data:"
                            countDataClass = 0
                            for data in rows["DataClasses"]:
                                countDataClass += 1
                                if countDataClass == 1:
                                    stringAnsw += f" {data}"
                                else:
                                    stringAnsw += f", {data}"
                        if rows.get("IsFabricated"):
                            stringAnsw += f"\n🤔 IsFabricated: {rows['IsFabricated']}"
                        if rows.get("IsSensitive"):
                            stringAnsw += f"\n👀 IsSensitive: {rows['IsSensitive']}"
                        if rows.get("IsRetired"):
                            stringAnsw += f"\n🎉 IsRetired: {rows['IsRetired']}"
                        if rows.get("IsSpamList"):
                            stringAnsw += f"\n🗑 IsSpamList: {rows['IsSpamList']}"
                        if rows.get("Description"):
                            stringAnsw += f"\n\n📝 Description: {rows['Description']}"
                        if rows.get("PwnCount"):
                            stringAnsw += f"\n\n👁 {rows['PwnCount']}"
                    elif service == 1:
                        stringAnsw += f"🔴 Page: {offset} / {countRow} Paste found\n"
                        if rows.get("Source"):
                            stringAnsw += f"\n📌 Source: {rows['Source']}"
                        if rows.get("Id"):
                            stringAnsw += f"\n🆔 ID: {rows['Id']}"
                        if rows.get("Title"):
                            stringAnsw += f"\n🔤 Title: {rows['Title']}"
                        if rows.get("Date"):
                            stringAnsw += f"\n📅 Date: {rows['Date']}"
                        if rows.get("EmailCount"):
                            stringAnsw += f"\n\n👁 {rows['EmailCount']}"
                    break

            array_kb = []
            array_kb.append([])
            if int(offset) > 1:
                array_kb[-1].append(InlineKeyboardButton("⬅️", callback_data=f"{cache}Inline§{msg}§{str(int(offset) - 1)}"))
            if int(offset) > 10:
                array_kb[-1].append(InlineKeyboardButton("⏪", callback_data=f"{cache}Inline§{msg}§{str(int(offset) - 10)}"))
            if int(offset) < (int(countRow) - 10):
                array_kb[-1].append(InlineKeyboardButton("⏩", callback_data=f"{cache}Inline§{msg}§{str(int(offset) + 10)}"))
            if int(offset) < int(countRow):
                array_kb[-1].append(InlineKeyboardButton("➡️", callback_data=f"{cache}Inline§{msg}§{str(int(offset) + 1)}"))

            array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])

            keyboardBreached = InlineKeyboardMarkup(array_kb)
            await context.bot.send_message(
                chat_id=chat_id,
                text=stringAnsw,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
                reply_markup=keyboardBreached
            )

        elif r.status_code == 400:
            await context.bot.send_message(chat_id, text=_("Bad request — the account does not comply with an acceptable format (i.e. it's an empty string) "))
        elif r.status_code == 403:
            await context.bot.send_message(chat_id, text=_("Forbidden — no user agent has been specified in the request"))
        elif r.status_code == 404:
            await context.bot.send_message(chat_id, text=_("Not found — Great! The account could not be found and has therefore not been pwned 😇"))
        elif r.status_code == 429:
            await context.bot.send_message(chat_id, text=_("Too many requests — the rate limit has been exceeded"))
        else:
            await context.bot.send_message(chat_id, text=f"Error {r.status_code}")

def safepass(password):
    password = password.encode()
    hashed = hashlib.sha1(password).hexdigest().upper()
    response = requests.get(f'https://api.pwnedpasswords.com/range/{hashed[:5]}')
    hashes = (line.split(':') for line in response.text.splitlines())
    for suffix, count in hashes:
        if hashed.endswith(suffix):
            return int(count)
    return 0


# Define error handler
async def error(update: Update, context: CallbackContext):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=_("❌ An error has occurred. Try later."))

# Define init function
async def init(update: Update, context: CallbackContext):
    chat_id = update.effective_message.chat_id
    text = update.effective_message.text if update.effective_message else update.callback_query.data
    
    utils.open_db()
    user = utils.get_user(chat_id)
    if not user:
        get_service_enabled = utils.get_user_service(chat_id)
        if get_service_enabled == 0:
            str_service_enabled = "Breaches"
        elif get_service_enabled == 1:
            str_service_enabled = "Pastes"
        else:
            str_service_enabled = "Password"
        keyboard_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("📖 Guide"), callback_data="guide"), InlineKeyboardButton(_("ℹ️ Various info"), callback_data="info")],
            [InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text=_("Welcome {userName}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\nhttps://haveibeenpwned.com\n\nActual service: {str_service_enabled}\n👷‍♂️ You can change the service on the settings").format(userName=update.effective_user.first_name, str_service_enabled=str_service_enabled),
            reply_markup=keyboard_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        utils.insert_user(chat_id, update.effective_user.language_code)
        lang_bot = utils.get_bot_lang(chat_id)
        utils.set_bot_lang(lang_bot, chat_id)
        return False
    else:
        lang_bot = utils.get_bot_lang(chat_id)
        utils.set_bot_lang(lang_bot, chat_id)
        if user['banned'] == 1:
            await context.bot.send_message(chat_id, text=_("You've been banned, you can not use this bot anymore. To check if your account/password has been compromised, go to https://haveibeenpwned.com"))
            return False
        elif user['status'] == "feedback":
            if update.message:
                if update.message.text == "/cancel" or update.message.text == "cancel":
                    await context.bot.send_message(chat_id, text=_("❌ Feedback canceled"))
                    utils.update_user_status(chat_id, 'feedback_canceled')
                else:
                    await context.bot.forward_message(chat_id=67292456, from_chat_id=chat_id, message_id=update.message.message_id)
                    await context.bot.send_message(chat_id, text=_("✅ Thanks for your feedback 👍 It was forwarded to developers."))
                    utils.update_user_status(chat_id, 'feedback_sent')
                return False
            else:
                return True
        elif user['status'] == "donate":
            if update.message:
                testo = update.message.text
                if testo == "/cancel" or testo == "❌ Cancel" or testo == "❌ cancel":
                    await context.bot.send_message(chat_id, text=_("Ok, canceled ✅"), reply_markup=ReplyKeyboardRemove())
                    utils.update_user_status(chat_id, 'cancel')
                elif testo == "€1":
                    await send_invoice(update, context, 1.00)
                elif testo == "€5":
                    await send_invoice(update, context, 5.00)
                elif testo == "€15":
                    await send_invoice(update, context, 15.00)
                elif testo == "€50":
                    await send_invoice(update, context, 50.00)
                elif testo.isdigit():
                    await send_invoice(update, context, float(testo))
                else:
                    await context.bot.send_message(chat_id, text=_("Choose how much you would like to donate through the menu button below:"))
                return False
        else:
            return True


async def donate(update: Update, context: CallbackContext):
    if await init(update, context):
        keyboardMarkup_back = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤙 Donate with Telegram Pay", callback_data="tgPay")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ])
        await update.message.reply_text(
            "Support this project by donating a coffee\n\n"
            "🅿️ Paypal: paypal.me/garboh\n\n"
            "☕️ Ko-Fi: ko-fi.com/garboh\n\n"
            "💎 TON: ton://transfer/UQD2QG5TBujZLZisfb12x54Anba_q3G_B58HoI5LNLqgmSK1\n\n"
            "Or use the Payments on Telegram: a new secure and fast way to donate and support our project.",
            reply_markup=keyboardMarkup_back,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

async def send_invoice(update: Update, context: CallbackContext, amount: float):
    chat_id = update.message.chat_id
    
    utils.update_user_status(chat_id, 'invoice_recived')
    title = "Donation to Pwned Robot"
    description = "Support the @pwned_robot Telegram Bot. Your donation will help us cover the cost of our server and keep this service free."
    payload = "pwned-support-bot"
    provider_token = PAYMENT_TOKEN
    currency = "EUR"
    prices = [LabeledPrice("Donation", int(amount * 100))]
    photo_url = "https://garbo.tech/img/portfolio/pwnedrobot.png"
    
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        start_parameter="support-pwned",
        currency=currency,
        prices=prices,
        photo_url=photo_url
    )
    await context.bot.send_message(chat_id, text="Here is your invoice. Tap now the Pay button and complete the payment.", reply_markup=ReplyKeyboardRemove())


async def inline_query(update: Update, context: CallbackContext):
    if await init(update, context):
        args = update.callback_query.data.split('§')
        query = update.callback_query
        chat_id = query.message.chat_id
        text = query.data
        keyboardMarkup_info = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("🛠 SourceCode"), url="https://github.com/garboh/pwned_robot"), InlineKeyboardButton(_("😇 Thanks to"), callback_data="info_thanks")],
            [InlineKeyboardButton(_("💪 Donate"), callback_data="info_donate"), InlineKeyboardButton(_("📬 Feedback"), callback_data="info_feedback")],
            [InlineKeyboardButton(_("🔙 Back"), callback_data="back_start")]
        ])
        keyboardMarkup_infoback = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("🔙 Back"), callback_data="info_back")]
        ])
        keyboardMarkup_back = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("🔙 Back"), callback_data="back")]
        ])
        keyboardMarkup_backstart = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("🔙 Back"), callback_data="back_start")]
        ])
        keyboardMarkup_settings = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service"), InlineKeyboardButton("👀 Privacy", callback_data="settings_privacy")],
            [InlineKeyboardButton("🗣 Bot language", callback_data="botlang")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
        ])
        
        if text == "info":
            await context.bot.edit_message_text(
                text=_("Hey there 😊\nHere you can find info about me, about those who have contributed to this project and about all my other bots.\n\nThis Bot is completely free and Open Source: https://github.com/garboh/pwned_robot"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardMarkup_info
            )
        elif text == "botlang":
            keyboard_lang = InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🌐 Translate bot"), url="https://www.transifex.com/hack-and-news/have-i-been-pwned")],
                [InlineKeyboardButton(_("🔙 Back"), callback_data="settings")]
            ])
            await context.bot.edit_message_text(
                text=_("Right now the bot is only available in English. There are already translators who are perfecting localized versions of the bot.\nIf you want to help us, join the team of translators on Transifex too!"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboard_lang
            )
        elif text == "info_thanks":
            await context.bot.edit_message_text(
                text=_("Special thanks to <a href='https://en.wikipedia.org/wiki/Troy_Hunt'>Troy Hunt</a> (haveibeenpwned.com Owner) who mentioned us on the <a href='https://haveibeenpwned.com/API/Consumers'>official website</a> \n\nAnd thanks also to whoever is working on translating this bot. Yep, you can help us to transale this bot on <a href='https://www.transifex.com/hack-and-news/have-i-been-pwned'>Transifex</a>"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardMarkup_infoback
            )
        elif text == "info_donate":
            infoback = InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🤙 Donate with Telegram Pay"), callback_data="tgPay")],
                [InlineKeyboardButton(_("🔙 Back"), callback_data="info_back")]
            ])
            await context.bot.edit_message_text(
                text=_("Support this project by donating a coffee\n\n🅿️ Paypal: paypal.me/garboh\n\n☕️ Ko-Fi: ko-fi.com/garboh\n\n💎 TON: ton://transfer/UQD2QG5TBujZLZisfb12x54Anba_q3G_B58HoI5LNLqgmSK1\n\nOr use the Payments on Telegram: a new secure and fast way to danate and supporting our project."),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=infoback
            )
        elif text == "info_feedback":
            await context.bot.edit_message_text(
                text=_("Tell what we can improve to make this bot better or /cancel"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML
            )
            utils.update_user_status(chat_id, 'feedback')
        elif text == "feedback_cancel":
            utils.update_user_status(chat_id, 'feedback_canceled')
            await context.bot.edit_message_text(
                text=_("Here I am, at your service! 💪"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboardMarkup_info
            )
        elif text == "guide":
            GUIDE_STR = _("<b>What have i been pwned is?</b>\nHave i been pwned is a website that allows Internet users to check whether their personal data has been compromised by data breaches.\n\n<b>What @pwned_robot is?</b>\n@pwned_robot use Have i been pwned API to use this service on Telegram.\n\n<b>How to use?</b>\nIs simply to use. There are 3 services available to check your accounts or passwords.\nTo change one service you just go to the bot settings from a menu button — then tap on services — <i>select the service you want to check</i>\n\nOther services will be supported ASAP.")
            await context.bot.edit_message_text(
                text=GUIDE_STR,
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardMarkup_backstart
            )
        elif text == "settings":
            await context.bot.edit_message_text(
                text=_("Here you can change the bot settings"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardMarkup_settings
            )
        elif text == "settings_privacy":
            row = utils.get_user(chat_id)
            if row:
                notify = row['notify']
                privacyStatus = "ON" if notify else "OFF"
                privacyStatusRev = "OFF" if notify else "ON"
                keyboardMarkup_privacy = InlineKeyboardMarkup([
                    [InlineKeyboardButton(privacyStatusRev, callback_data="privacy_change")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
                await context.bot.edit_message_text(
                    text=_("No sensitive data, information you send to @pwned_robot will be saved, shared or sold internally or by third parties. Any email or phone number you write here in chat with the bot will only be processed and sent to haveibeenpwned.com to produce a response regarding your account status, but we do not save it in our database and we do not sell it to companies to make money. We care about your privacy!\nAccording to haveibeenpwned.com the source code of this bot is free and open source.\n\nHere you can change the bot privacy:\nRecive notifications about future updates\n\nNotifications: <b>{}</b>").format(privacyStatus),
                    chat_id=chat_id,
                    message_id=query.message.message_id,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboardMarkup_privacy
                )
            else:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=True, text="An error has occurred")
        elif text == "privacy_change":
            row = utils.get_user(chat_id)
            if row:
                notify = row['notify']
                new_notify = 0 if notify else 1
                utils.update_user_notify(chat_id, new_notify)
                privacyStatus = "ON" if new_notify else "OFF"
                privacyStatusRev = "OFF" if new_notify else "ON"
                keyboardMarkup_privacy = InlineKeyboardMarkup([
                    [InlineKeyboardButton(privacyStatusRev, callback_data="privacy_change")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
                await context.bot.edit_message_text(
                    text=_("No sensitive data, information you send to @pwned_robot will be saved, shared or sold internally or by third parties. Any email or phone number you write here in chat with the bot will only be processed and sent to haveibeenpwned.com to produce a response regarding your account status, but we do not save it in our database and we do not sell it to companies to make money. We care about your privacy!\nAccording to haveibeenpwned.com the source code of this bot is free and open source.\n\nHere you can change the bot privacy:\nRecive notifications about future updates\n\nNotifications: <b>{}</b>").format(privacyStatus),
                    chat_id=chat_id,
                    message_id=query.message.message_id,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboardMarkup_privacy
                )
            else:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=True, text="An error has occurred")
        elif text == "settings_service":
            row = utils.get_user(chat_id)
            if row:
                service = row['service']
                breachedaccount = "✅" if service == 0 else ""
                pasteaccount = "✅" if service == 1 else ""
                checkpsw = "✅" if service == 2 else ""
                actualService = "breachedaccount" if service == 0 else "pasteaccount" if service == 1 else "checkpsw"
                str_service_enabled = "Breaches" if service == 0 else "Pastes" if service == 1 else "Password"
                keyboardMarkup_services = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{breachedaccount} breachedaccount", callback_data="breachedaccount"),
                     InlineKeyboardButton(f"{pasteaccount} pasteaccount", callback_data="pasteaccount"),
                     InlineKeyboardButton(f"{checkpsw} checkpsw", callback_data="checkpsw")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
                await context.bot.edit_message_text(
                    text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email or <a href='https://t.me/HIBP_updates/34'>phone number</a> to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{str_service_enabled}</b>").format(str_service_enabled=str_service_enabled),
                    chat_id=chat_id,
                    message_id=query.message.message_id,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=keyboardMarkup_services
                )
            else:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=True, text="An error has occurred")
        elif text == "breachedaccount":
            try:
                utils.update_user_service(chat_id, 0)
                actualService = "breachedaccount"
                keyboardMarkup_services = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ breachedaccount", callback_data="breachedaccount"),
                     InlineKeyboardButton("pasteaccount", callback_data="pasteaccount"),
                     InlineKeyboardButton("checkpsw", callback_data="checkpsw")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
                await context.bot.edit_message_text(
                    text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email or <a href='https://t.me/HIBP_updates/34'>phone number</a> to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService),
                    chat_id=chat_id,
                    message_id=query.message.message_id,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=keyboardMarkup_services
                )
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
            except:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False, text="❌ already in use")
        elif text == "pasteaccount":
            try:
                utils.update_user_service(chat_id, 1)
                actualService = "pasteaccount"
                keyboardMarkup_services = InlineKeyboardMarkup([
                    [InlineKeyboardButton("breachedaccount", callback_data="breachedaccount"),
                     InlineKeyboardButton("✅ pasteaccount", callback_data="pasteaccount"),
                     InlineKeyboardButton("checkpsw", callback_data="checkpsw")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
                await context.bot.edit_message_text(
                    text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email or <a href='https://t.me/HIBP_updates/34'>phone number</a> to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService),
                    chat_id=chat_id,
                    message_id=query.message.message_id,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=keyboardMarkup_services
                )
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
            except:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False, text="❌ already in use")
        elif text == "checkpsw":
            try:
                utils.update_user_service(chat_id, 2)
                actualService = "checkpsw"
                keyboardMarkup_services = InlineKeyboardMarkup([
                    [InlineKeyboardButton("breachedaccount", callback_data="breachedaccount"),
                     InlineKeyboardButton("pasteaccount", callback_data="pasteaccount"),
                     InlineKeyboardButton("✅ checkpsw", callback_data="checkpsw")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
                await context.bot.edit_message_text(
                    text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email or <a href='https://t.me/HIBP_updates/34'>phone number</a> to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService),
                    chat_id=chat_id,
                    message_id=query.message.message_id,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=keyboardMarkup_services
                )
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
            except:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False, text="❌ already in use")
        elif text == "info_back":
            await context.bot.edit_message_text(
                text=_("Hey there 😊\nHere you can find info about me, about those who have contributed to this project and about all my other bots.\n\nThis Bot is completely free and Open Source: https://github.com/garboh/pwned_robot"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardMarkup_info
            )
        elif text == "tgPay":
            pulsanti = ReplyKeyboardMarkup([
                [KeyboardButton(_("€1")), KeyboardButton(_("€5"))],
                [KeyboardButton(_("€15")), KeyboardButton(_("€50"))],
                [KeyboardButton(_("❌ Cancel"))]
            ])
            await context.bot.edit_message_text(
                text=_("Well Done! Telegram Pay is the best secure and fast way to donation and support our project. We use the Stripe Provider, if you want to know more how Telegram Pay works read this: https://core.telegram.org/bots/payments"),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await context.bot.send_message(
                text=_("Choose how much you would like to donate:"),
                chat_id=chat_id,
                parse_mode=ParseMode.HTML,
                reply_markup=pulsanti
            )
            utils.update_user_status(chat_id, 'donate')
        elif text in ["back_start", "back"]:
            service = utils.get_user_service(chat_id)
            str_service_enabled = "Breaches" if service == 0 else "Pastes" if service == 1 else "Password"
            keyboardMarkup = InlineKeyboardMarkup([
                [InlineKeyboardButton(_("📖 Guide"), callback_data="guide"), InlineKeyboardButton(_("ℹ️ Various info"), callback_data="info")],
                [InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")]
            ])
            await context.bot.edit_message_text(
                text=_("Welcome back {userName}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\nhttps://haveibeenpwned.com\n\nActual service: {str_service_enabled}\n👷‍♂️ You can change the service on the settings").format(userName=update.callback_query.from_user.first_name, str_service_enabled=str_service_enabled),
                chat_id=chat_id,
                message_id=query.message.message_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardMarkup
            )
        elif args[0] == "breachedInline":
            msg = args[1]
            offset = int(args[2])
            try:
                with open(f'./cache/breached/{chat_id}.json') as json_file:
                    json_object = json.load(json_file)
            except:
                customheaders = {
                    'User-Agent': 'Pwnage-Checker-For-Telegram',
                    'api-version': '3',
                    'Accept': 'application/vnd.haveibeenpwned.v3+json',
                    'hibp-api-key': '203c8676a5894f549fcc42caa13d7e9a'
                }
                url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote_plus(msg)}?truncateResponse=false"
                r = requests.get(url, headers=customheaders)
                if r.status_code == 200:
                    json_object = r.json()
                    with open(f'./cache/breached/{chat_id}.json', 'w', encoding='utf-8') as f:
                        json.dump(json_object, f, ensure_ascii=False, indent=4)

            stringAnsw = ""

            countRow = 0
            countRowIn = 0

            for row in json_object:
                countRow += 1

            for rows in json_object:
                countRowIn += 1
                if countRowIn == offset:
                    if rows.get("LogoPath"):
                        stringAnsw += f"<a href='{rows['LogoPath']}'>🔴</a> Page: {offset} / {countRow} Breach found \n"
                    else:
                        stringAnsw += f"🔴 Page: {offset} / {countRow} Breach found \n"
                    if rows.get("IsVerified"):
                        if rows['IsVerified']:
                            stringAnsw += "\n✅ Breach verified"
                        else:
                            stringAnsw += "\n🚫 Breach not verified"
                    if rows.get("Name"):
                        stringAnsw += f"\nℹ️ {rows['Name']}"
                    if rows.get("Title"):
                        stringAnsw += f"\n🔤 {rows['Title']}"
                    if rows.get("Domain"):
                        stringAnsw += f"\n🌐 {rows['Domain']}"
                    if rows.get("BreachDate"):
                        stringAnsw += f"\n📅 Breach on: {rows['BreachDate']}"
                    if rows.get("AddedDate"):
                        stringAnsw += f"\n➕ Added on: {rows['AddedDate']}"
                    if rows.get("ModifiedDate"):
                        stringAnsw += f"\n📆 Modified on: {rows['ModifiedDate']}"
                    if rows.get("DataClasses"):
                        stringAnsw += "\n📚 Data:"
                        countDataClass = 0
                        for data in rows["DataClasses"]:
                            countDataClass += 1
                            if countDataClass == 1:
                                stringAnsw += f" {data}"
                            else:
                                stringAnsw += f", {data}"
                    if rows.get("IsVerified"):
                        stringAnsw += f"\n✅ IsVerified: {rows['IsVerified']}"
                    if rows.get("IsFabricated"):
                        stringAnsw += f"\n🤔 IsFabricated: {rows['IsFabricated']}"
                    if rows.get("IsSensitive"):
                        stringAnsw += f"\n👀 IsSensitive: {rows['IsSensitive']}"
                    if rows.get("IsRetired"):
                        stringAnsw += f"\n🎉 IsRetired: {rows['IsRetired']}"
                    if rows.get("IsSpamList"):
                        stringAnsw += f"\n🗑 IsSpamList: {rows['IsSpamList']}"
                    if rows.get("Description"):
                        stringAnsw += f"\n\n📝 Description: {rows['Description']}"
                    if rows.get("PwnCount"):
                        stringAnsw += f"\n\n👁 {rows['PwnCount']}"
                    break

            array_kb = []
            array_kb.append([])
            if int(offset) > 1:
                array_kb[-1].append(InlineKeyboardButton("⬅️", callback_data=f"breachedInline§{msg}§{str(int(offset) - 1)}"))
            if int(offset) > 10:
                array_kb[-1].append(InlineKeyboardButton("⏪", callback_data=f"breachedInline§{msg}§{str(int(offset) - 10)}"))
            if int(offset) < (int(countRow) - 10):
                array_kb[-1].append(InlineKeyboardButton("⏩", callback_data=f"breachedInline§{msg}§{str(int(offset) + 10)}"))
            if int(offset) < int(countRow):
                array_kb[-1].append(InlineKeyboardButton("➡️", callback_data=f"breachedInline§{msg}§{str(int(offset) + 1)}"))

            array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])

            keyboardBreached = InlineKeyboardMarkup(array_kb)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                text=stringAnsw,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
                reply_markup=keyboardBreached
            )

        elif args[0] == "pasteInline":
            msg = args[1]
            offset = int(args[2])
            try:
                with open(f'./cache/paste/{chat_id}.json') as json_file:
                    json_object = json.load(json_file)
            except:
                customheaders = {
                    'User-Agent': 'Pwnage-Checker-For-Telegram',
                    'api-version': '3',
                    'Accept': 'application/vnd.haveibeenpwned.v3+json',
                    'hibp-api-key': '203c8676a5894f549fcc42caa13d7e9a'
                }
                url = f"https://haveibeenpwned.com/api/v3/pasteaccount/{urllib.parse.quote_plus(msg)}"
                r = requests.get(url, headers=customheaders)
                if r.status_code == 200:
                    json_object = r.json()
                    with open(f'./cache/paste/{chat_id}.json', 'w', encoding='utf-8') as f:
                        json.dump(json_object, f, ensure_ascii=False, indent=4)

            stringAnsw = ""

            countRow = 0
            countRowIn = 0

            for row in json_object:
                countRow += 1

            for rows in json_object:
                countRowIn += 1
                if countRowIn == offset:
                    stringAnsw += f"🔴 Page: {offset} / {countRow} Paste found\n"
                    if rows.get("Source"):
                        stringAnsw += f"\n📌 Source: {rows['Source']}"
                    if rows.get("Id"):
                        stringAnsw += f"\n🆔 ID: {rows['Id']}"
                    if rows.get("Title"):
                        stringAnsw += f"\n🔤 Title: {rows['Title']}"
                    if rows.get("Date"):
                        stringAnsw += f"\n📅 Date: {rows['Date']}"
                    if rows.get("EmailCount"):
                        stringAnsw += f"\n\n👁 {rows['EmailCount']}"
                    break

            array_kb = []
            array_kb.append([])
            if int(offset) > 1:
                array_kb[-1].append(InlineKeyboardButton("⬅️", callback_data=f"pasteInline§{msg}§{str(int(offset) - 1)}"))
            if int(offset) > 10:
                array_kb[-1].append(InlineKeyboardButton("⏪", callback_data=f"pasteInline§{msg}§{str(int(offset) - 10)}"))
            if int(offset) < (int(countRow) - 10):
                array_kb[-1].append(InlineKeyboardButton("⏩", callback_data=f"pasteInline§{msg}§{str(int(offset) + 10)}"))
            if int(offset) < int(countRow):
                array_kb[-1].append(InlineKeyboardButton("➡️", callback_data=f"pasteInline§{msg}§{str(int(offset) + 1)}"))

            array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])

            keyboardBreached = InlineKeyboardMarkup(array_kb)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                text=stringAnsw,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboardBreached
            )
        else:
            await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=True, text="bot is under construction")
    await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, show_alert=False)

async def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload != "pwned-support-bot":
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Thank you for your donation!")

# Register handlers
def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("donate", donate))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, testo))
    application.add_handler(CallbackQueryHandler(inline_query))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_error_handler(error)

# Main function to start the bot
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    register_handlers(application)
    application.run_polling()

if __name__ == "__main__":
    main()
