import sqlite3
from aiogram import types
import os
from log import create_logger
from config import db_DIR, bot
from typing import NamedTuple
from datetime import datetime

logger = create_logger(__name__)
if not os.path.isdir(db_DIR):
    os.mkdir(db_DIR)
conn = sqlite3.connect(db_DIR + "db.db", check_same_thread=False)
cursor = conn.cursor()

class UserInfo(NamedTuple):
    id: int
    user_id: int
    username: str
    firstname: str
    bot_username: str
    balance: int
    all_time_balance: int
    cash_circulation: int
    percentage: int
    percentage_edit_type: str
    btc_wallet: str
    usdt_wallet: str
    is_banned: str

class PromocodeInfo(NamedTuple):
    id: int
    name: str
    user_id: int
    ammount: int
    activation_count: int
    deposit: int
    ubt: str 

class DB:

    # Перемнные с названиями таблиц, создано для удобства
    users_table = "users"
    unconfirmed_users_table = "unconfirmed_users"
    bot_info = "bot_info"
    promocodes = "promocodes"
    deposits = "deposits"
    
    def run():
        """
        Создание таблиц БД
        """
        # Создание основной таблицы с пользователями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id                      INTEGER PRIMARY KEY,
                user_id                 INTEGER NOT NULL,
                tg_username             TEXT,
                tg_firstname            TEXT,
                username                TEXT,
                balance                 REAL NOT NULL,
                all_time_balance        REAL NOT NULL,
                cash_circulation        REAL,
                percentage              INTEGER,
                percentage_edit_type    TEXT,
                btc_wallet              TEXT,
                usdt_wallet             TEXT,
                _is_banned              TEXT
                
            )
        ''')
        conn.commit()

        # Создание таблицы с не подтвержденными пользователями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unconfirmed_users (
                id             INTEGER PRIMARY KEY,
                user_id        INTEGER NOT NULL,
                tg_username    TEXT,
                state          TEXT NOT NULL,
                experience     TEXT NOT NULL,
                forum_url      TEXT NOT NULL
            )
        ''')
        conn.commit()

        # Создание таблицы с информацией для бота
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_info (
                id             INTEGER PRIMARY KEY,
                actual_url        TEXT,
                info              TEXT,
                all_time_balance  REAL,
                promo_activations INTEGER,
                deposits          INTEGER
            )
        ''')
        conn.commit()

        # Создает строку в bot_info, должно срабатывать только при первом запуске
        cursor.execute("SELECT actual_url, info FROM bot_info")
        exists = cursor.fetchall()
        if not exists:
            cursor.execute('INSERT INTO bot_info (actual_url, info, all_time_balance, promo_activations, deposits) VALUES (?, ?, ?, ?, ?)', ("REPLACE_ME", "REPLACE_ME", 0, 0, 0))
            conn.commit()

        # Создание таблицы с промокодами
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                id                  INTEGER PRIMARY KEY,
                name                TEXT NOT NULL,
                user_id             INTEGER NOT NULL,
                amount              INTEGER NOT NULL,
                activation_count    INTEFER NOT NULL,
                deposit             INTEGER NOT NULL,
                ubt                 TEXT NOT NULL   
            )
        ''')
        conn.commit()

        # Создание таблицы с депозитами
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deposits (
                id                  INTEGER PRIMARY KEY,
                worker_id           INTEGER NOT NULL,
                amount              REAL NOT NULL,
                amountUSD           REAL NOT NULL,       
                mamonth_login       TEXT NOT NULL,
                token               TEXT NOT NULL,
                domain              TEXT NOT NULL,
                date                TEXT NOT NULL,
                hash                TEXT NOT NULL,
                country             TEXT NOT NULL
            )
        ''')
        conn.commit()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER,
                deposit INTEGER DEFAULT (1),
                support INTEGER DEFAULT (1) 
            )
        ''')
        conn.commit()

    


    def insert_new_user(user_id: int, tg_username: str, forum_url: str, exp: str):
        """
        Вставка пользователя в БД, для ожидания подтвеждения
        """

        cursor.execute(
            'INSERT INTO unconfirmed_users (user_id, tg_username, state, forum_url, experience) '
            'VALUES (?, ?, ?, ?, ?)',
            (user_id, tg_username, "wait", forum_url, exp))
        conn.commit()


    def insert(user_id: int, tg_username: str, tg_firstname: str):
        """
        Вставка пользователя в основную БД после подтверждения
        """
        is_user = DB.get(user_id=user_id, data="user_id", table=DB.users_table)
        if is_user is None:
            cursor.execute(
                'INSERT INTO users (user_id, tg_username, tg_firstname, username, balance, cash_circulation, percentage, percentage_edit_type, _is_banned, all_time_balance) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, tg_username, tg_firstname, tg_firstname, 0, 0, 50, "auto", "False", 0))
            conn.commit()
            
            cursor.execute(
                'INSERT INTO settings (user_id, deposit, support) '
                'VALUES (?, ?, ?)',
                (user_id, 1, 1))
            conn.commit()
        else:
            pass
             
    def add_notif_user(user_id: int):
        cursor.execute(
            f"SELECT * FROM settings WHERE user_id = ?",
            (user_id, ))
        
        result = cursor.fetchone()
        if result is None:
            cursor.execute(
                'INSERT INTO settings (user_id, deposit, support) '
                'VALUES (?, ?, ?)',
                (user_id, 1, 1))
            conn.commit()
    
    def get_user_where_promocode(user_id: str):
        cursor.execute(f"SELECT * FROM promocodes WHERE name = ?", (user_id, ))
        data = cursor.fetchone()
        return PromocodeInfo(
            id=data[0],
            name=data[1],
            user_id=data[2],
            ammount=data[3],
            activation_count=data[4],
            deposit=data[5],
            ubt=data[6]
        )
    
    def get_user_where_user_id(user_id: str):
        cursor.execute(f"SELECT * FROM users WHERE user_id = ?", (user_id, ))
        data = cursor.fetchone()
        
        return UserInfo(
            id=data[0],
            user_id=data[1],
            username=data[2],
            firstname=data[3],
            bot_username=data[4],
            balance=data[5],
            all_time_balance=data[6],
            cash_circulation=data[7],
            percentage=data[8],
            percentage_edit_type=data[9],
            btc_wallet=data[10],
            usdt_wallet=data[11],
            is_banned=data[12]

        )
    
    
    def get_notif_user(user_id: int):
        cursor.execute(
            f"SELECT * FROM settings WHERE user_id = ?",
            (user_id, )
        )
        
        result = cursor.fetchone()
        return result
    
    def edit_notif_user(user_id: int, column: str, data: int):
        try:
            cursor.execute(f"UPDATE settings SET {column} = ? WHERE user_id = ?", (data, user_id))
            conn.commit()
            return True
        except Exception:
            return False
               
    def insert_promo(user_id: int, name: str, ubt: str, amount: int):
        """
        Вставка промика в БД
        """
        
        cursor.execute(
            'INSERT INTO promocodes (user_id, name, amount, ubt, activation_count, deposit) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, name, amount, ubt, 0, 0))
        conn.commit()


    def get(user_id: int, data: str, table: str):
        """
        Получние данных из БД по user_id
        """
        
        cursor.execute(
            f"SELECT {data} FROM {table} WHERE user_id = ?",
            (user_id, ))
        
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None
    
    def get_without_user_id(data: str, table: str):
        """
        Получние данных из БД без user_id
        """
        
        cursor.execute(f"SELECT {data} FROM {table}")
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None
        
    
    def get_all_user_id(user_id: int, data: str, table: str):
        """
        Получение всех данных из БД по user_id и data 
        """
        
        cursor.execute(f"SELECT {data} FROM {table} WHERE user_id = ?", (user_id, ))
        fetch = cursor.fetchall()
        result = []
        for item in fetch:
            item = item[0]
            result.append(item)
        return result
    
    def get_all(data: str, table: str):
        """
        Получение всех данных из БД по data
        """
        cursor.execute(f"SELECT {data} FROM {table}")
        fetch = cursor.fetchall()
        result = []
        for item in fetch:
            item = item[0]
            result.append(item)
        return result

    def delete(user_id: int, table: str):
        """
        Удаление строчки из БД
        """
        
        try:
            cursor.execute(f"DELETE from {table} where user_id = ?", (user_id,))
            conn.commit()
            return True
        except Exception:
            return False

    def update(user_id: int, column: str, new_data: str, table: str):
        """
        Обновление данных в БД
        """
        
        try:
            cursor.execute(f"UPDATE {table} SET {column} = ? WHERE user_id = ?", (new_data, user_id))
            conn.commit()
            return True
        except Exception:
            return False
    
    def update_without_user_id(column: str, new_data: str, table: str):
        """
        Обновление данных в БД
        """
        
        try:
            cursor.execute(f"UPDATE {table} SET {column} = ?", (new_data, ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
    
    def update_rrr(user_id: int, promocode: str, activation_count: int, deposit: int, worker_balance: int, domain: str, data: dict):
        today = datetime.now()
        
        #user/notstat
        cursor.execute(f"UPDATE promocodes SET activation_count = activation_count + ? WHERE name = ?", (activation_count, promocode))
        conn.commit()
        
        cursor.execute(f"UPDATE promocodes SET deposit = deposit + ? WHERE name = ?", (deposit, promocode))
        conn.commit()
        
        cursor.execute(f"UPDATE users SET balance = balance + ? WHERE user_id = ?", (worker_balance, user_id))
        conn.commit()
        
        cursor.execute(f"UPDATE users SET all_time_balance = all_time_balance + ? WHERE user_id = ?", (deposit, user_id))
        conn.commit()
        ########################################
        
        #bot
        print(round(float(deposit), 3))
        cursor.execute(f"UPDATE bot_info SET all_time_balance = all_time_balance + ? WHERE actual_url = ?", (deposit, domain))
        conn.commit()
        
        cursor.execute(f"UPDATE bot_info SET promo_activations = promo_activations + ? WHERE actual_url = ?", (1, domain))
        conn.commit()
        
        cursor.execute(f"UPDATE bot_info SET deposits = deposits + ? WHERE actual_url = ?", (1, domain))
        conn.commit()
        
        #deposit table
        cursor.execute(
            'INSERT INTO deposits (worker_id, amount, mamonth_login, token, domain, date, hash, country, amountUSD)'
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                user_id,
                float(data['amount']), 
                str(data["mammothLogin"]), 
                str(data["token"]), 
                str(data["domain"]), 
                today, 
                str(data["txHash"]), 
                str(data["mammothCountry"]), 
                str(data["amountUsd"])
            )
        )

        conn.commit()
        return True
    
    

    
