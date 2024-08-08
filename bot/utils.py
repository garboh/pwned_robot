import MySQLdb
from bot.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import bot.sql_queries as sql_queries

def open_db():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

def get_user_lang(chat_id):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.GET_USER_LANG, (chat_id,))
    lang = cur.fetchone()
    db.close()
    return lang[0] if lang else None

def set_user_lang(lang, chat_id):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.SET_USER_LANG, (lang, chat_id))
    db.commit()
    db.close()

def set_user_status(status, chat_id):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.UPDATE_USER_STATUS, (status, chat_id))
    db.commit()
    db.close()

def get_user(chat_id):
    db = open_db()
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(sql_queries.GET_USER, (chat_id,))
    user = cur.fetchone()
    db.close()
    return user

def get_user_status(chat_id):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.GET_USER_STATUS, (chat_id,))
    status = cur.fetchone()
    db.close()
    return status[0] if status else None

def get_user_service(chat_id):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.GET_USER_SERVICE, (chat_id,))
    service = cur.fetchone()
    db.close()
    return service[0] if service else 0

def insert_user(chat_id, lang):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.INSERT_USER, (chat_id, lang))
    db.commit()
    db.close()

def update_user_status(chat_id, status):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.UPDATE_USER_STATUS, (status, chat_id))
    db.commit()
    db.close()

def update_user_service(chat_id, service):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.UPDATE_USER_SERVICE, (service, chat_id))
    db.commit()
    db.close()

def update_user_notify(chat_id, service):
    db = open_db()
    cur = db.cursor()
    cur.execute(sql_queries.UPDATE_USER_NOTIFY, (service, chat_id))
    db.commit()
    db.close()

def get_bot_lang(chat_id):
    # Assuming you want to fetch language for the bot, similar to user language
    return get_user_lang(chat_id)

def set_bot_lang(lang, chat_id):
    # Assuming you want to set language for the bot, similar to user language
    set_user_lang(lang, chat_id)