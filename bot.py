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
from httpcache import CachingHTTPAdapter
import json
import certifi
import urllib3
from urllib.request import Request, urlopen
from telegram import *
from telegram.ext import *
from telegram.ext.dispatcher import run_async
import gettext
from gettext import ngettext

http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

#translation file
en = gettext.translation('pwned_robot', localedir='locale', languages=['en'])
#it = gettext.translation('pwned_robot', localedir='locale', languages=['it'])

# xgettext -d pwned_robot -o pwned_robot.pot pwned.py


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
    try:
        keyboard= InlineKeyboardMarkup([[InlineKeyboardButton(_("🔙 Back"), callback_data="back_start")]])
        bot.sendMessage(update.message.chat_id, reply_markup = keyboard, text=_("❌ An error has occurred. Try later.\n\nThe developers have just been notified. If the problem persists do not hesitate to use the feedback form, thanks. 📬"))
        bot.sendMessage(chat_id=67292456, text='Update "%s" caused error "%s"' % (update, error))
        openDb()
        cur.execute("UPDATE `user` SET `status`='action_cancel' WHERE `id`='{}'".format(update.message.from_user.id))
        end()
    except:
        pass


def openDb():
    global db
    global cur

    db = MySQLdb.connect(host="",      # your host, usually localhost
                         user="",           # your username
                         passwd="",  # your password
                         db="",         # name of the data base
                         charset='utf8mb4',
                         use_unicode=True)
    cur = db.cursor()
    
def getBotLang(chat=0):
    cur.execute("SELECT `lang` FROM `user` WHERE `chat_id`={}".format(chat))
    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return None

def setBotLang(lang, chat):
    global _
    _ = en.gettext
       
    cur.execute("UPDATE `user` SET `lang`='{}' WHERE `chat_id`={}".format(lang, chat))

def init(bot, update):
    openDb()
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
        strServiceEnabled = getStrService(bot, update)
        keyboardMarkup = InlineKeyboardMarkup([[InlineKeyboardButton(_("📖 Guide"), callback_data="guide"),InlineKeyboardButton(_("ℹ️ Various info"), callback_data="info")],[InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")]])
        bot.sendMessage(update.message.chat_id, text=_("Welcome {userName}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\nhttps://haveibeenpwned.com\n\n{strServiceEnabled}").format(userName=update.message.from_user.first_name,strServiceEnabled=strServiceEnabled), reply_markup=keyboardMarkup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        cur.execute("INSERT INTO `user`(`chat_id`, `date_time`) VALUES ({},now())".format(chat_id))
        langBot = getBotLang(chat_id)
        setBotLang(langBot, chat_id)
        return False
    else:
        langBot = getBotLang(chat_id)
        setBotLang(langBot, chat_id)
        if row[3]==1:
            bot.sendMessage(update.message.chat_id, text=_("You've been banned, you can not use this bot anymore. To check if your account/password has been compromised, go to https://haveibeenpwned.com"))
            return False
        elif row[4]=="feedback":
            if update.message:
                if update.message.text=="/cancel" or update.message.text=="cancel":
                    bot.sendMessage(update.message.chat_id, text=_("❌ Feedback canceled"))
                    cur.execute("UPDATE `user` SET `status`='feedback_canceled' WHERE `chat_id`={}".format(chat_id))
                else:
                    bot.forwardMessage(chat_id=67292456, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
                    bot.sendMessage(update.message.chat_id, text=_("✅ Thanks for your feedback 👍 It was forwarded to developers."))
                    cur.execute("UPDATE `user` SET `status`='feedback_sent' WHERE `chat_id`={}".format(chat_id))
                return False
            else:
                return True
        else:
            return True

def cancel(bot, update):
    if init(bot, update):
        bot.sendMessage(update.message.chat_id, text=_("No action to cancel"))
    end()
    
def getStrService(chatId):
    cur.execute("SELECT service FROM user WHERE `chat_id`={}".format(chatId))
    row = cur.fetchone()
    strServiceEnabled = _("breachedaccount is enabled, write your email to check if you have an account that has been compromised")
    if row:
        if row[0]==1:
            strServiceEnabled = _("pasteaccount is enabled, write your email to see all paste found")
        if row[0]==2:
            strServiceEnabled = _("checkpsw is enabled, write your password to check if this password has been compromised")
    return strServiceEnabled
    
def start(bot, update):
    if init(bot, update):
        strServiceEnabled = getStrService(update.message.chat_id)
        keyboardMarkup = InlineKeyboardMarkup([[InlineKeyboardButton(_("📖 Guide"), callback_data="guide"),InlineKeyboardButton(_("ℹ️ Various info"), callback_data="info")],[InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")]])
        bot.sendMessage(update.message.chat_id, text=_("Welcome back {userName}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\nhttps://haveibeenpwned.com\n\n{strServiceEnabled}").format(userName=update.message.from_user.first_name, strServiceEnabled=strServiceEnabled), reply_markup=keyboardMarkup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    end()
    
def donate(bot, update):
    if init(bot, update):
        keyboardMarkup_back = InlineKeyboardMarkup([[InlineKeyboardButton(_("🔙 Back"), callback_data="back")]]) 
        bot.sendMessage(update.message.chat_id, text=_("Support the project by donating a coffee\n\n🅿️ paypal.me/garboh"), reply_markup=keyboardMarkup_back, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    end()
    
def guide(bot, update):
    if init(bot, update):
        keyboardMarkup_back = InlineKeyboardMarkup([[InlineKeyboardButton(_("🔙 Back"), callback_data="back")]]) 
        GUIDE_STR = _("<b>What have i been pwned is?</b>\nHave i been pwned is a website that allows Internet users to check whether their personal data has been compromised by data breaches.\n\n<b>What @pwned_robot is?</b>\n@pwned_robot use Have i been pwned API to use this service on Telegram. Yep is a forked!\n\n<b>How to use?</b>\nIs simply to use. There are 3 services available to check your accounts or passwords.\nTo change one service you just go to the bot settings from a menu button — then tap on services — <i>select the service you want to check</i>\n\nOther services will be supported ASAP.")
        bot.sendMessage(update.message.chat_id, text="{}".format(GUIDE_STR), reply_markup=keyboardMarkup_back, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    end()
    
def text(bot, update):
    checkPwned(bot, update, update.message.chat_id, update.message.text, 1)

def checkPwned(bot, update, chat_id, msg, offset):
    if init(bot, update):
        cur.execute("SELECT `service` FROM `user` WHERE `chat_id`={}".format(chat_id))
        row = cur.fetchone()
        if row:
            service = row[0]
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
                actualService = "checkpsw"
                count = safepass(msg)
                if count == 0:
                    bot.sendMessage(chat_id, text=_("<b>Good news — no pwnage found!</b>\n\nThis password wasn't found in any of the Pwned Passwords loaded into Have I Been Pwned. That doesn't necessarily mean it's a good password, merely that it's not indexed on this site."),parse_mode=ParseMode.HTML)
                else:
                    bot.sendMessage(chat_id, text=_("<b>Oh no — pwned!</b>\n\nThis password has been seen {} times before.\nThis password has previously appeared in a data breach and should never be used. If you've ever used it anywhere before, change it!").format(count),parse_mode=ParseMode.HTML)
                normal = False
            if normal:    
                customheaders = {'User-Agent': 'Pwnage-Checker-For-Telegram', 'api-version': '3', 'Accept': 'application/vnd.haveibeenpwned.v3+json', 'hibp-api-key': 'your hibp api key'}
                url = "https://haveibeenpwned.com/api/v3/{}/{}{}".format(actualService, urllib.parse.quote_plus(msg), truncate)
                r = http.request('GET', url, headers=customheaders)

                
                if r.status == 200:
                    json_object = json.loads(r.data)
                    json_query = json.dumps(json_object)
                    with open('./cache/{}/{}.json'.format(cache,chat_id), 'w', encoding='utf-8') as f:
                        json.dump(json_object, f, ensure_ascii=False, indent=4)
                    #cur.execute("UPDATE `user` SET `json`='{}' WHERE `chat_id`={}".format(json_query, chat_id))
                    stringAnsw = ""
                    if service == 1:
                        countRow = 0
                        countRowIn = 0
                        for row in json_object:
                            countRow += 1
                        
                        for rows in json_object:
                            countRowIn += 1
                            if countRowIn == offset:
                                stringAnsw += "🔴 Page: {} / {} Paste  found\n".format(offset, countRow)
                                if rows.get("Source"):
                                    stringAnsw += "\n📌 Source: {}".format(rows["Source"])
                                if rows.get("Id"):
                                    stringAnsw += "\n🆔 ID: {}".format(rows["Id"])
                                if rows.get("Title"):
                                    stringAnsw += "\n🔤 Title: {}".format(rows["Title"])
                                if rows.get("Date"):
                                    stringAnsw += "\n📅 Date: {}".format(rows["Date"])
                                if rows.get("EmailCount"):
                                    stringAnsw += "\n👁‍🗨  EmailCount: {}".format(rows["EmailCount"])
                                break
                        array_kb=[]
                        array_kb.append([])
                        if int(offset) < (int(countRow) - 10):
                            array_kb[-1].append(InlineKeyboardButton("⏩", callback_data="pasteInline§{}§{}".format(msg, str(int(offset)+10))))
                        if int(offset) < int(countRow):
                            array_kb[-1].append(InlineKeyboardButton("➡️", callback_data="pasteInline§{}§{}".format(msg, str(int(offset)+1))))
                        
                        array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])
                        
                        keyboardBreached = InlineKeyboardMarkup(array_kb)
                        bot.sendMessage(chat_id, text="{}".format(str(stringAnsw)), parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=keyboardBreached)
                    
                    
                    elif service ==0:
                        countRow = 0
                        countRowIn = 0
                        for rows in json_object:
                            countRow += 1
                        
                        for rows in json_object:
                            countRowIn += 1
                            if countRowIn == offset:
                                stringAnsw += "🔴 Page: {} / {} Breach found \n".format(offset, countRow)
                                if rows.get("Name"):
                                    stringAnsw += "\nℹ️ Name: {}".format(rows["Name"])
                                if rows.get("Title"):
                                    stringAnsw += "\n🔤 Title: {}".format(rows["Title"])
                                if rows.get("Domain"):
                                    stringAnsw += "\n🌐 Domain: {}".format(rows["Domain"])
                                if rows.get("BreachDate"):
                                    stringAnsw += "\n📅 BreachDate: {}".format(rows["BreachDate"])
                                if rows.get("AddedDate"):
                                    stringAnsw += "\n➕ AddedDate: {}".format(rows["AddedDate"])
                                if rows.get("ModifiedDate"):
                                    stringAnsw += "\n📆 ModifiedDate: {}".format(rows["ModifiedDate"])
                                if rows.get("DataClasses"):
                                    stringAnsw += "\n📚 DataClasses:"
                                    countDataClass = 0
                                    for data in rows["DataClasses"]:
                                        countDataClass += 1
                                        if countDataClass == 1:
                                            stringAnsw += " {}".format(data)
                                        else:
                                            stringAnsw += ", {}".format(data)
                                if rows.get("IsVerified"):
                                    stringAnsw += "\n✅ IsVerified: {}".format(rows["IsVerified"])
                                if rows.get("IsFabricated"):
                                    stringAnsw += "\n🤔 IsFabricated: {}".format(rows["IsFabricated"])
                                if rows.get("IsSensitive"):
                                    stringAnsw += "\n👀 IsSensitive: {}".format(rows["IsSensitive"])
                                if rows.get("IsRetired"):
                                    stringAnsw += "\n🎉 IsRetired: {}".format(rows["IsRetired"])
                                if rows.get("IsSpamList"):
                                    stringAnsw += "\n🗑 IsSpamList: {}".format(rows["IsSpamList"])
                                if rows.get("Description"):
                                    stringAnsw += "\n\n📝 Description: {}".format(rows["Description"])
                                if rows.get("LogoPath"):
                                    stringAnsw += "\n\n🧩 LogoPath: {}".format(rows["LogoPath"])
                                if rows.get("PwnCount"):
                                    stringAnsw += "\n\n👁‍🗨 PwnCount: {}".format(rows["PwnCount"])
                                break
                        array_kb=[]
                        array_kb.append([])
                        if int(offset) < (int(countRow) - 10):
                            array_kb[-1].append(InlineKeyboardButton("⏩", callback_data="breachedInline§{}§{}".format(msg, str(int(offset)+10))))
                        if int(offset) < int(countRow):
                            array_kb[-1].append(InlineKeyboardButton("➡️", callback_data="breachedInline§{}§{}".format(msg, str(int(offset)+1))))
                        
                        array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])
                        
                        keyboardBreached = InlineKeyboardMarkup(array_kb)
                        bot.sendMessage(chat_id, text="{}".format(str(stringAnsw)), parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=keyboardBreached)
                elif r.status == 400:
                   bot.sendMessage(chat_id, text=_("Bad request — the account does not comply with an acceptable format (i.e. it's an empty string) "))
                elif r.status == 403:
                   bot.sendMessage(chat_id, text=_("Forbidden — no user agent has been specified in the request"))
                elif r.status == 404:
                   bot.sendMessage(chat_id, text=_("Not found — the account could not be found and has therefore not been pwned"))
                elif r.status == 429:
                   bot.sendMessage(chat_id, text=_("Too many requests — the rate limit has been exceeded"))
                else:
                    bot.sendMessage(chat_id, text="Error {}".format(r.status_code))
  
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
        args = update.callback_query.data.split('§')
        query = update.callback_query
        chat_id = query.message.chat_id
        text = query.data
        keyboardMarkup_info = InlineKeyboardMarkup([[InlineKeyboardButton(_("📖 Developer"), callback_data="info_dev"),InlineKeyboardButton(_("😇 Thanks to"), callback_data="info_thanks")],[InlineKeyboardButton(_("🤖 Other bots"), callback_data="info_bots")],[InlineKeyboardButton(_("💪 Donate"), callback_data="info_donate"),InlineKeyboardButton(_("📬 Feedback"), callback_data="info_feedback")],[InlineKeyboardButton(_("🔙 Back"), callback_data="back_start")]])
        keyboardMarkup_infoback = InlineKeyboardMarkup([[InlineKeyboardButton(_("🔙 Back"), callback_data="info_back")]])  
        keyboardMarkup_back = InlineKeyboardMarkup([[InlineKeyboardButton(_("🔙 Back"), callback_data="back")]]) 
        keyboardMarkup_backstart = InlineKeyboardMarkup([[InlineKeyboardButton(_("🔙 Back"), callback_data="back_start")]]) 
        keyboardMarkup_settings = InlineKeyboardMarkup([[InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service"),InlineKeyboardButton("👀 Privacy", callback_data="settings_privacy")],[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]) 
        if text == "info":
            bot.editMessageText(text=_("Hey there 😊\nHere you can find info about me, about those who have contributed to this project and about all my other bots.\n\nThis Bot is completely free and Open Source: https://github.com/garboh/pwned_robot"), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_info)
        elif text == "info_dev":
            bot.editMessageText(text=_("I'm 20 years old, I'm currently studying IT Engineer at <a href='https://en.wikipedia.org/wiki/University_of_Padua'>UniPD</a>, in Italy. I've developed many Telegram bots and webApps. \n\nI developed this bot to check in a quickly and easily way if an account has been compromised in a data breach."), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=keyboardMarkup_infoback)
        elif text == "info_thanks":      
            bot.editMessageText(text=_("Special thanks to haveibeenpwned.com \n\nYou can help us to transale this bot on <a href='https://www.transifex.com/hack-and-news/have-i-been-pwned'>Transifex</a>"), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=keyboardMarkup_infoback)
        elif text == "info_bots":           
            bot.editMessageText(text=_("I've developed some other bots, useful and funny:\n🔹 @CiuchinoCalls call it on Telegram voicecall to listen awesome music. \n🔹 @langTLA_bot change the entire Telegram interface into one of the official or minority languages available. \n🔹 @CiuchinoBot Have fun with a stupid AI. Many functions for private chat, groups and supergroups."), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_infoback)
        elif text == "info_donate":
            bot.editMessageText(text=_("Support the project by donating a coffee\n\n🅿️ paypal.me/garboh"), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_infoback)
        elif text == "info_feedback":
            #!!! do not translate the /cancel comand
            bot.editMessageText(text=_("Tell what we can improve to make this bot better or /cancel"), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML)
            cur.execute("UPDATE `user` SET `status`='feedback' WHERE `chat_id`={}".format(chat_id))
        elif text == "feedback_cancel":
            cur.execute("UPDATE `user` SET `status`='feedback_canceled' WHERE `chat_id`={}".format(chat_id)) 
            bot.editMessageText(text=_("Here I am, at your service! 💪"), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_info)
        elif text == "guide":
            GUIDE_STR = _("<b>What have i been pwned is?</b>\nHave i been pwned is a website that allows Internet users to check whether their personal data has been compromised by data breaches.\n\n<b>What @pwned_robot is?</b>\n@pwned_robot use Have i been pwned API to use this service on Telegram. Yep is a forked!\n\n<b>How to use?</b>\nIs simply to use. There are 3 services available to check your accounts or passwords.\nTo change one service you just go to the bot settings from a menu button — then tap on services — <i>select the service you want to check</i>\n\nOther services will be supported ASAP.")
            bot.editMessageText(text="{}".format(GUIDE_STR), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_backstart)
        elif text == "settings":
            bot.editMessageText(text=_("Here you can change the bot settings"), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_settings)
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
                bot.editMessageText(text=_("Here you can change the bot privacy:\nRecive notifications about future updates\n\nNotifications: <b>{}</b>").format(privacyStatus), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_privacy)
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
                bot.editMessageText(text=_("Here you can change the bot privacy:\nRecive notifications about future updates\n\nNotifications: <b>{}</b>").format(privacyStatus), chat_id=chat_id, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_privacy)
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
                bot.editMessageText(text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
            else:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="An error has ocurred")
        elif text == "breachedaccount":
            try:
                cur.execute("UPDATE `user` SET `service`='0' WHERE `chat_id`={}".format(chat_id))
                actualService = "breachedaccount"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("✅ breachedaccount", callback_data="breachedaccount"),InlineKeyboardButton("pasteaccount", callback_data="pasteaccount"),InlineKeyboardButton("checkpsw", callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅") 
            except:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="❌  already in use") 
        elif text == "pasteaccount":
            try:
                cur.execute("UPDATE `user` SET `service`='1' WHERE `chat_id`={}".format(chat_id))
                actualService = "pasteaccount"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("breachedaccount", callback_data="breachedaccount"),InlineKeyboardButton("✅ pasteaccount", callback_data="pasteaccount"),InlineKeyboardButton("checkpsw", callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅") 
            except:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="❌  already in use") 
        elif text == "checkpsw":
            try:
                cur.execute("UPDATE `user` SET `service`='2' WHERE `chat_id`={}".format(chat_id))
                actualService = "checkpsw"
                keyboardMarkup_services = InlineKeyboardMarkup([[InlineKeyboardButton("breachedaccount", callback_data="breachedaccount"),InlineKeyboardButton("pasteaccount", callback_data="pasteaccount"),InlineKeyboardButton("✅ checkpsw", callback_data="checkpsw")],[InlineKeyboardButton("🔙 Back", callback_data="settings")]]) 
                bot.editMessageText(text=_("Here you can change the Bot service, by default breachedaccount is enabled.\n\n🟠 Choose \"breachedaccount\" service to return a <b>list of all breaches</b> of a particular account that has been involved in. So just send your email to check if you have an account that has been compromised in a data breach.\n\n🟣 Choose \"pasteaccount\" service to return <b>all pastes</b> for an account.  Write your email and verify.\n\n🔵 Choose \"checkpsw\" service to return if your password has been compromised. So write your <b>password</b> to check if has been seen somewhere.\n\nActual service: <b>{actualService}</b>").format(actualService=actualService), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_services)
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅") 
            except:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="❌  already in use") 
        elif text == "info_back":
            bot.editMessageText(text=_("Hey there 😊\nHere you can find info about me, about those who have contributed to this project and about all my other bots.\n\nThis Bot is completely free and Open Source: https://github.com/garboh/pwned_robot"), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup_info)
        elif text == "back_start" or text == "back"  :
            strServiceEnabled = getStrService(update.callback_query.message.chat_id)    
            keyboardMarkup = InlineKeyboardMarkup([[InlineKeyboardButton(_("📖 Guide"), callback_data="guide"),InlineKeyboardButton(_("ℹ️ Various info"), callback_data="info")],[InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")]])
            bot.editMessageText(text=_("Welcome back {userName}! \nWith this Bot you can <b>check if you have an account that has been compromised in a data breach</b>.\nhttps://haveibeenpwned.com\n\n{strServiceEnabled}").format(userName=update.callback_query.from_user.first_name,strServiceEnabled=strServiceEnabled), chat_id=chat_id, disable_web_page_preview=True, message_id=query.message.message_id,parse_mode=ParseMode.HTML, reply_markup=keyboardMarkup)
        elif args[0] == "breachedInline":
            
            msg = args[1]
            offset = int(args[2])
            
            
            with open('./cache/breached/{}.json'.format(update.callback_query.message.chat_id)) as json_file:
                json_object = json.load(json_file)
 
            stringAnsw = ""
        
            countRow = 0
            countRowIn = 0

            for row in json_object:
                countRow += 1
                
            for rows in json_object:
                countRowIn += 1
                if countRowIn == offset:
                    stringAnsw += "🔴 Page: {} / {} Breach found \n".format(offset, countRow)
                    if rows.get("Name"):
                        stringAnsw += "\nℹ️ Name: {}".format(rows["Name"])
                    if rows.get("Title"):
                        stringAnsw += "\n🔤 Title: {}".format(rows["Title"])
                    if rows.get("Domain"):
                        stringAnsw += "\n🌐 Domain: {}".format(rows["Domain"])
                    if rows.get("BreachDate"):
                        stringAnsw += "\n📅 BreachDate: {}".format(rows["BreachDate"])
                    if rows.get("AddedDate"):
                        stringAnsw += "\n➕ AddedDate: {}".format(rows["AddedDate"])
                    if rows.get("ModifiedDate"):
                        stringAnsw += "\n📆 ModifiedDate: {}".format(rows["ModifiedDate"])
                    if rows.get("DataClasses"):
                        stringAnsw += "\n📚 DataClasses:"
                        countDataClass = 0
                        for data in rows["DataClasses"]:
                            countDataClass += 1
                            if countDataClass == 1:
                                stringAnsw += " {}".format(data)
                            else:
                                stringAnsw += ", {}".format(data)
                    if rows.get("IsVerified"):
                        stringAnsw += "\n✅ IsVerified: {}".format(rows["IsVerified"])
                    if rows.get("IsFabricated"):
                        stringAnsw += "\n🤔 IsFabricated: {}".format(rows["IsFabricated"])
                    if rows.get("IsSensitive"):
                        stringAnsw += "\n👀 IsSensitive: {}".format(rows["IsSensitive"])
                    if rows.get("IsRetired"):
                        stringAnsw += "\n🎉 IsRetired: {}".format(rows["IsRetired"])
                    if rows.get("IsSpamList"):
                        stringAnsw += "\n🗑 IsSpamList: {}".format(rows["IsSpamList"])
                    if rows.get("Description"):
                        stringAnsw += "\n\n📝 Description: {}".format(rows["Description"])
                    if rows.get("LogoPath"):
                        stringAnsw += "\n\n🧩 LogoPath: {}".format(rows["LogoPath"])
                    if rows.get("PwnCount"):
                        stringAnsw += "\n\n👁‍🗨 PwnCount: {}".format(rows["PwnCount"])
                    break 

            array_kb=[]
            array_kb.append([])
            if int(offset) > 1:
                array_kb[-1].append(InlineKeyboardButton("⬅️", callback_data="breachedInline§{}§{}".format(msg, str(int(offset)-1))))
            if int(offset) > 10:
                array_kb[-1].append(InlineKeyboardButton("⏪", callback_data="breachedInline§{}§{}".format(msg, str(int(offset)-10))))
            if int(offset) < (int(countRow) - 10):
                array_kb[-1].append(InlineKeyboardButton("⏩", callback_data="breachedInline§{}§{}".format(msg, str(int(offset)+10))))
            if int(offset) < int(countRow):
                array_kb[-1].append(InlineKeyboardButton("➡️", callback_data="breachedInline§{}§{}".format(msg, str(int(offset)+1))))
            
            array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])
            
            keyboardBreached = InlineKeyboardMarkup(array_kb)
            bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{}".format(str(stringAnsw)), parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=keyboardBreached)

        elif args[0] == "pasteInline":
            
            msg = args[1]
            offset = int(args[2])
            
            
            with open('./cache/paste/{}.json'.format(update.callback_query.message.chat_id)) as json_file:
                json_object = json.load(json_file)
 
            stringAnsw = ""
        
            countRow = 0
            countRowIn = 0

            for row in json_object:
                countRow += 1
                
            for rows in json_object:
                countRowIn += 1
                if countRowIn == offset:
                    stringAnsw += "🔴 Page: {} / {} Paste  found\n".format(offset, countRow)
                    if rows.get("Source"):
                        stringAnsw += "\n📌 Source: {}".format(rows["Source"])
                    if rows.get("Id"):
                        stringAnsw += "\n🆔 ID: {}".format(rows["Id"])
                    if rows.get("Title"):
                        stringAnsw += "\n🔤 Title: {}".format(rows["Title"])
                    if rows.get("Date"):
                        stringAnsw += "\n📅 Date: {}".format(rows["Date"])
                    if rows.get("EmailCount"):
                        stringAnsw += "\n👁‍🗨  EmailCount: {}".format(rows["EmailCount"])
                    break 

            array_kb=[]
            array_kb.append([])
            if int(offset) > 1:
                array_kb[-1].append(InlineKeyboardButton("⬅️", callback_data="pasteInline§{}§{}".format(msg, str(int(offset)-1))))
            if int(offset) > 10:
                array_kb[-1].append(InlineKeyboardButton("⏪", callback_data="pasteInline§{}§{}".format(msg, str(int(offset)-10))))
            if int(offset) < (int(countRow) - 10):
                array_kb[-1].append(InlineKeyboardButton("⏩", callback_data="pasteInline§{}§{}".format(msg, str(int(offset)+10))))
            if int(offset) < int(countRow):
                array_kb[-1].append(InlineKeyboardButton("➡️", callback_data="pasteInline§{}§{}".format(msg, str(int(offset)+1))))
            
            array_kb.append([InlineKeyboardButton(_("🔙 Back"), callback_data="back_start"), InlineKeyboardButton(_("👷‍♂️ Service"), callback_data="settings_service")])
            
            keyboardBreached = InlineKeyboardMarkup(array_kb)
            bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{}".format(str(stringAnsw)), parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=keyboardBreached)

            

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
    updater = Updater("your bot's token here")

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
