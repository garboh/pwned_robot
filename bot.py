#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import platform
import hashlib
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
import urllib
import MySQLdb
import time
import requests
import json
from urllib.request import Request, urlopen
from telegram import *
from telegram.ext import *
from telegram.ext.dispatcher import run_async

keyboardMarkup = InlineKeyboardMarkup([[InlineKeyboardButton("📖 Guide", callback_data="guide"),InlineKeyboardButton("ℹ️ Various info", callback_data="info")],[InlineKeyboardButton("⚙️ Settings", callback_data="settings")]])
GUIDE_STR = "<b>How to use?</b>\n\n1️⃣ To find out if an account has been breached use the \"<b>breachedaccount</b>\" service in the settings and then send the email address of that account.\n2️⃣ To know if there is a 'paste' file you have to go in the settings and change the service in \"<b>pasteaccount</b>\" and then send the email address of that account\n3️⃣ You can also check if a password has been compromised, in this case change the service to \"<b>checkpsw</b>\"\n\nOther services will be supported ASAP."

def error(bot, update, error):
    try:
        bot.sendMessage(update.message.chat.id, text = '❗️ Update "%s" caused error "%s"\n\n➡Ask to bot developer⬅️' % (update, error))
    except:
        pass
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def init(bot, update):
    global db
    global cur

    db = MySQLdb.connect(host="",      # your host, usually localhost
                         user="",           # your username
                         passwd="#",  # your password
                         db="",            # name of the data base
                         charset='utf8mb4',
                         use_unicode=True)
    cur = db.cursor()

    global chat_id
    
    try:
        chat_id = update.message.chat_id
        text = update.message.text
    except:
        chat_id = update.callback_query.message.chat_id
        query = update.callback_query
        text = query.data
        
    cur.execute("SELECT * FROM user WHERE `chat_id`={}".format(chat_id))
    row = cur.fetchone()
    if not row:
        bot.sendMessage(update.message.chat_id, text="Welcome {}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\n\nhttps://haveibeenpwned.com".format(update.message.from_user.first_name), reply_markup=keyboardMarkup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        cur.execute("INSERT INTO `user`(`chat_id`, `date_time`) VALUES ({},now())".format(chat_id))
        return False
    else:
        if row[3]==1:
            bot.sendMessage(update.message.chat_id, text="You've been banned, you can not use this bot anymore. To check if your account/password has been compromised, go to https://haveibeenpwned.com")
            return False
        elif row[4]=="feedback":
            if update.message:
                if update.message.text=="/cancel" or update.message.text=="cancel":
                    bot.sendMessage(update.message.chat_id, text="❌ Feedback canceled")
                    cur.execute("UPDATE `user` SET `status`='feedback_canceled' WHERE `chat_id`={}".format(chat_id))
                else:
                    bot.forwardMessage(chat_id=<your ID>, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
                    bot.sendMessage(update.message.chat_id, text="✅ Thanks for your feedback 👍 It was forwarded to developers.")
                    cur.execute("UPDATE `user` SET `status`='feedback_sent' WHERE `chat_id`={}".format(chat_id))
                return False
            else:
                return True
        else:
            return True

def cancel(bot, update):
    if init(bot, update):
        bot.sendMessage(update.message.chat_id, text="No action to cancel ")
    end()
    
def start(bot, update):
    if init(bot, update):
        bot.sendMessage(update.message.chat_id, text="Welcome back {}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\n\nhttps://haveibeenpwned.com".format(update.message.from_user.first_name), reply_markup=keyboardMarkup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    end()
    
def donate(bot, update):
    if init(bot, update):
        keyboardMarkup_back = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]) 
        bot.sendMessage(update.message.chat_id, text="Support the project by donating a coffee\n\n🅿️ paypal.me/garboh", reply_markup=keyboardMarkup_back, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    end()
    
def guide(bot, update):
    if init(bot, update):
        keyboardMarkup_back = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]) 
        bot.sendMessage(update.message.chat_id, text="{}".format(GUIDE_STR), reply_markup=keyboardMarkup_back, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    end()
    
def text(bot, update):
    if init(bot, update):
        time.sleep(1)
        cur.execute("SELECT `service` FROM `user` WHERE `chat_id`={}".format(chat_id))
        row = cur.fetchone()
        if row:
            service = row[0]
            normal = True
            if service == 0:
                actualService = "breachedaccount"
            elif service == 1:
                actualService = "pasteaccount"
            elif service == 2:
                actualService = "checkpsw"
                count = safepass(update.message.text)
                if count == 0:
                    bot.sendMessage(update.message.chat_id, text="<b>Good news — no pwnage found!</b>\n\nThis password wasn't found in any of the Pwned Passwords loaded into Have I Been Pwned. That doesn't necessarily mean it's a good password, merely that it's not indexed on this site.",parse_mode=ParseMode.HTML)
                else:
                    bot.sendMessage(update.message.chat_id, text="<b>Oh no — pwned!</b>\n\nThis password has been seen {} times before.\nThis password has previously appeared in a data breach and should never be used. If you've ever used it anywhere before, change it! ".format(count),parse_mode=ParseMode.HTML)
                normal = False
            if normal:
                headers = {'User-Agent': 'Pwnage-Checker-For-Telegram', 'api-version': '2', 'Accept': 'application/vnd.haveibeenpwned.v2+json'}
                url = "https://haveibeenpwned.com/api/v2/{}/{}".format(actualService, urllib.parse.quote_plus(update.message.text))
                r = requests.get(url, headers=headers, verify=True)
                
                if r.status_code == 200:
                    json_object = json.loads(r.content)
                    stringAnsw = ""
                    if service == 1:
                        for rows in json_object:
                            stringAnsw += "\n\n📌 Source: {}\n🆔 ID: {}\n🔤 Title: {}\n📅 Date: {}\n👁‍🗨  EmailCount: {}".format(rows["Source"], rows["Id"], rows["Title"],rows["Date"], rows["EmailCount"])
                        bot.sendMessage(update.message.chat_id, text="{}".format(str(stringAnsw)))
                    elif service ==0:
                        bot.sendMessage(update.message.chat_id, text="{}".format(str(json.loads(r.content))))
                elif r.status_code == 400:
                   bot.sendMessage(update.message.chat_id, text="Bad request — the account does not comply with an acceptable format (i.e. it's an empty string) ")
                elif r.status_code == 403:
                   bot.sendMessage(update.message.chat_id, text="Forbidden — no user agent has been specified in the request")
                elif r.status_code == 404:
                   bot.sendMessage(update.message.chat_id, text="Not found — the account could not be found and has therefore not been pwned")
                elif r.status_code == 429:
                   bot.sendMessage(update.message.chat_id, text="Too many requests — the rate limit has been exceeded")
    end()
    
def safepass(passwd):
    passwd = passwd.encode()
    hashed = hashlib.sha1(passwd).hexdigest().upper()
    page = requests.get(
        'https://api.pwnedpasswords.com/range/' + hashed[:5],
        headers={
            'User-Agent': 'Pwnage-Checker-For-Telegram'
        }
    )
    for line in page.text.split('\n'):
        suffix, count = line.split(':')
        count = int(count)
        if hashed.endswith(suffix):
            if count > 0:
                return count
            break
    return 0
    
def inline_query(bot, update):
    if init(bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id
        text = query.data
        keyboardMarkup_info = InlineKeyboardMarkup([[InlineKeyboardButton("📖 Developer", callback_data="info_dev"),InlineKeyboardButton("😇 Thanks to", callback_data="info_thanks")],[InlineKeyboardButton("🤖 Other bots", callback_data="info_bots")],[InlineKeyboardButton("💪 Donate", callback_data="info_donate"),InlineKeyboardButton("📬 Feedback", callback_data="info_feedback")],[InlineKeyboardButton("🔙 Back", callback_data="back_start")]])
        keyboardMarkup_infoback = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="info_back")]])  
        keyboardMarkup_back = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]) 
        keyboardMarkup_backstart = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]) 
        keyboardMarkup_settings = InlineKeyboardMarkup([[InlineKeyboardButton("👷‍♂️ Service", callback_data="settings_service"),InlineKeyboardButton("👀 Privacy", callback_data="settings_privacy")],[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]) 
        if text == "info":
            bot.editMessageText(text="Hey there 😊\nHere you can find info about me, about those who have contributed to this project and about all my other bots.\n\nSource code: https://github.com/garboh/pwned_robot", chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_info)
        elif text == "info_dev":
            bot.editMessageText(text="I'm 18 years old, I'm currently studying Information Techonlogy in Padua, in Italy. I've developed many Telegram bots and webApps. \n\nI developed this bot to check in a quickly and easily way if an account has been compromised in a data breach.", chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_infoback)
        elif text == "info_thanks":      
            bot.editMessageText(text="Special thanks to haveibeenpwned.com \n\nTranslators:\nworking on it", chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_infoback)
        elif text == "info_bots":           
            bot.editMessageText(text="I've developed some other bots, useful and funny:\n🔹 @megachatbot Chat with people with the same preferences or with strangers randomly chosen! \n🔹 @CiuchinoCalls call it to listen awesome music \n🔹 @CiuchinoBot Have fun with jokes and insults. Many functions for private chat, groups and supergroups.", chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_infoback)
        elif text == "info_donate":
            bot.editMessageText(text="Support the project by donating a coffee\n\n🅿️ paypal.me/garboh", chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_infoback)
        elif text == "info_feedback":
            #keyboardMarkup_infofeedback = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="feedback_cancel")]])  
            #reply_markup=keyboardMarkup_infofeedback
            bot.editMessageText(text="Tell what we can improve to make this bot better or /cancel", chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML)
            cur.execute("UPDATE `user` SET `status`='feedback' WHERE `chat_id`={}".format(chat_id))
        elif text == "feedback_cancel":
            cur.execute("UPDATE `user` SET `status`='feedback_canceled' WHERE `chat_id`={}".format(chat_id)) 
            bot.editMessageText(text="Here I am, at your service! 💪", chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_info)
        elif text == "guide":
            bot.editMessageText(text="{}".format(GUIDE_STR), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_backstart)
        elif text == "settings":
            bot.editMessageText(text="Here you can change the bot settings", chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_settings)
        elif text == "settings_privacy":
            cur.execute("SELECT `notify` FROM `user` WHERE `chat_id`={}".format(chat_id))
            row = cur.fetchone()
            if row:
                notify = row[0]
                if notify == 0:
                    privacyStatus = "OFF"
                    privacyStatusRev = "ON"
                elif notify == 1:
                    privacyStatus = "ON"
                    privacyStatusRev = "OFF"
                keyboardMarkup_privacy = InlineKeyboardMarkup([[InlineKeyboardButton("{}".format(privacyStatusRev), callback_data="privacy_change")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text="Here you can change the bot privacy:\nRecive notifications about future updates\n\nNotifications: <b>{}</b>".format(privacyStatus), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_privacy)
            else:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="An error has ocurred")
        elif text == "privacy_change":
            cur.execute("SELECT `notify` FROM `user` WHERE `chat_id`={}".format(chat_id))
            row = cur.fetchone()
            if row:
                notify = row[0]
                if notify == 0:
                    cur.execute("UPDATE `user` SET `notify`='1' WHERE `chat_id`={}".format(chat_id))
                    privacyStatus = "ON"
                    privacyStatusRev = "OFF"
                elif notify == 1:
                    cur.execute("UPDATE `user` SET `notify`='0' WHERE `chat_id`={}".format(chat_id))
                    privacyStatus = "OFF"
                    privacyStatusRev = "ON"
                keyboardMarkup_privacy = InlineKeyboardMarkup([[InlineKeyboardButton("{}".format(privacyStatusRev), callback_data="privacy_change")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text="Here you can change the bot privacy:\nRecive notifications about future updates\n\nNotifications: <b>{}</b>".format(privacyStatus), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_privacy)
            else:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="An error has ocurred")
        elif text == "settings_service":
            cur.execute("SELECT `service` FROM `user` WHERE `chat_id`={}".format(chat_id))
            row = cur.fetchone()
            if row:
                service = row[0]
                breachedaccount =""
                pasteaccount =""
                checkpsw =""
                if service == 0:
                    actualService = "breachedaccount"
                    breachedaccount = "✅"
                elif service == 1:
                    actualService = "pasteaccount"
                    pasteaccount = "✅"
                elif service == 2:
                    actualService = "checkpsw"
                    checkpsw = "✅"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("{} breachedaccount".format(breachedaccount), callback_data="breachedaccount"),InlineKeyboardButton("{} pasteaccount".format(pasteaccount), callback_data="pasteaccount"),InlineKeyboardButton("{} checkpsw".format(checkpsw), callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text="Here you can change the service: \n\n🔹 Choose \"breachedaccount\" service to return a list of all breaches of a particular account that has been involved in.\n🔹 Choose \"pasteaccount\" service to return all pastes for an account.\n🔹 Choose \"checkpsw\" service to return if your password has been compromised.\n\nActual service: <b>{}</b>".format(actualService), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
            else:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="An error has ocurred")
        elif text == "breachedaccount":
            try:
                cur.execute("UPDATE `user` SET `service`='0' WHERE `chat_id`={}".format(chat_id))
                actualService = "breachedaccount"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("✅ breachedaccount", callback_data="breachedaccount"),InlineKeyboardButton("pasteaccount", callback_data="pasteaccount"),InlineKeyboardButton("checkpsw", callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text="Here you can change the service: \n\n🔹 Choose \"breachedaccount\" service to return a list of all breaches of a particular account that has been involved in.\n🔹 Choose \"pasteaccount\" service to return all pastes for an account.\n🔹 Choose \"checkpsw\" service to return if your password has been compromised.\n\nActual service: <b>{}</b>".format(actualService), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅") 
            except:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="❌  already in use") 
        elif text == "pasteaccount":
            try:
                cur.execute("UPDATE `user` SET `service`='1' WHERE `chat_id`={}".format(chat_id))
                actualService = "pasteaccount"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("breachedaccount", callback_data="breachedaccount"),InlineKeyboardButton("✅ pasteaccount", callback_data="pasteaccount"),InlineKeyboardButton("checkpsw", callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text="Here you can change the service: \n\n🔹 Choose \"breachedaccount\" service to return a list of all breaches of a particular account that has been involved in.\n🔹 Choose \"pasteaccount\" service to return all pastes for an account.\n🔹 Choose \"checkpsw\" service to return if your password has been compromised.\n\nActual service: <b>{}</b>".format(actualService), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅") 
            except:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="❌  already in use") 
        elif text == "checkpsw":
            try:
                cur.execute("UPDATE `user` SET `service`='2' WHERE `chat_id`={}".format(chat_id))
                actualService = "checkpsw"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("breachedaccount", callback_data="breachedaccount"),InlineKeyboardButton("pasteaccount", callback_data="pasteaccount"),InlineKeyboardButton("✅ checkpsw", callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text="Here you can change the service: \n\n🔹 Choose \"breachedaccount\" service to return a list of all breaches of a particular account that has been involved in.\n🔹 Choose \"pasteaccount\" service to return all pastes for an account.\n🔹 Choose \"checkpsw\" service to return if your password has been compromised.\n\nActual service: <b>{}</b>".format(actualService), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅") 
            except:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="❌  already in use") 
        elif text == "info_back":
            bot.editMessageText(text="Hey there 😊\nHere you can find info about me, about those who have contributed to this project and about all my other bots.\n\nSource code: https://github.com/garboh/pwned_robot", chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_info)
        elif text == "back_start":
            bot.editMessageText(text="Welcome back {}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\n\nhttps://haveibeenpwned.com".format(update.callback_query.from_user.first_name), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup)
        else:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="bot is under construction")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False)  
    end()        
    
def end():
    db.commit()
    db.close()
    
def main():
    if not platform.python_version().startswith('3'):
        print("Python version: "+platform.python_version())
        print("Python version not compatible! Required version 3")
        exit()
    print("pwned start!")
    
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("your token here")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", guide))
    dp.add_handler(CommandHandler("donate", donate))
    dp.add_handler(CommandHandler("cancel", cancel))
    
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(CallbackQueryHandler(inline_query))
    dp.add_handler(MessageHandler(Filters.text, text))

    # log all errors
    dp.add_error_handler(error)
    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
if __name__ == '__main__':
    main()
