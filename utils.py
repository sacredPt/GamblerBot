from io import StringIO
import logging
import sys

import requests
from config import *
from db import DB, cursor, conn
import api
from datetime import datetime
import asyncio

from pydantic import BaseModel
from log import create_logger


async def send_request_to_admin(msg: types.Message, forum_url: str, exp: str):
    """
    Отправка заявок о регистрации по ADMIN_ID (указываеться в config.ini)
    """
    
    
    btns = [
        [types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"user_request_decline?{msg.from_user.id}"), 
         types.InlineKeyboardButton(text="✅ Принять", callback_data=f"user_request_accept?{msg.from_user.id}")]
    ]
    text = f'''
⛄️Новая заявка в команду!
├👤Юзернейм пользователя: @{msg.from_user.username}
├🆔ID пользователя: <code>{msg.from_user.id}</code>
├💭Опыт работы: <code>{exp}</code>
└💭Ссылка на форум(lolz.live): <code>{forum_url}</code>
'''

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns),
        parse_mode='HTML'
    )


async def show_user_profile(call: types.CallbackQuery = None, msg: types.Message = None, msg2edit: types.Message = None):
    if call is not None:
        user_id = call.from_user.id
    elif msg is not None:
        user_id = msg.from_user.id

    btc_wallet, usdt_wallet = DB.get(user_id=user_id, data="btc_wallet", table=DB.users_table), DB.get(user_id=user_id, data="usdt_wallet", table=DB.users_table)
    if btc_wallet is None:
        btc_wallet = "Не привязан"
    if usdt_wallet is None:
        usdt_wallet = "Не привязан"
    
    text = f"""
<b>☃️ Профиль
├🆔Ваш ID: <code>{user_id}</code>
├🦋Ваш никнейм: <code>{DB.get(user_id=user_id, data="username", table=DB.users_table)}</code>
├💸Ваш баланс: <code>{DB.get(user_id=user_id, data="balance", table=DB.users_table)}$</code>
├💲Ваш процент с депозитов: <code>{DB.get(user_id=user_id, data="percentage", table=DB.users_table)}%</code>
├👛 Привязанные кошельки:
    └ BTC: <code>{btc_wallet}</code>
    └ USDT TRC-20: <code>{usdt_wallet}</code>

🧊Статистика
├💎Оборот: <code>{DB.get(user_id=user_id, data="cash_circulation", table=DB.users_table)}$</code></b>
"""

    profile_btns = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🦋 Изменить ник", callback_data="change_username"), types.InlineKeyboardButton(text="👛 Привязать кошелек", callback_data="link_wallet")],
        [types.InlineKeyboardButton(text="💸 Вывод средств", callback_data="payout")],
        [types.InlineKeyboardButton(text="❄️", callback_data="back_main")]
    ])
    await msg.answer(
        text=text,
        reply_markup=profile_btns,
        parse_mode='HTML'
    )

    


async def send_payout_to_admin(user_id: int, amount_of_payout: float, wallet_name: str):
    """
    Отправка заявок на вывод админу по CHANNEL_ID (указываеться в config.ini)
    """
    
    user_firstname = DB.get(user_id=user_id, data="tg_firstname", table=DB.users_table)
    user_name = DB.get(user_id=user_id, data="tg_username", table=DB.users_table)
    wallet = DB.get(user_id=user_id, data=f"{wallet_name.lower()}_wallet", table=DB.users_table)
    text = f"""
💰 Заявка на выплату
🆔 {user_firstname} / {user_id} / @{user_name}
⚡ Сумма: {amount_of_payout} $ 
💳 Кошелек:
└ {wallet_name}: {wallet}
            """
    
    send_payout_btns = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Отклонено", callback_data=f"payout_request_decline?{user_id}"), 
         types.InlineKeyboardButton(text="✅ Выплачено", callback_data=f"payout_request_accept?{user_id}")]
    ])


    await bot.send_message(
        chat_id=USERS_PAYOUTS,
        text=text,
        reply_markup=send_payout_btns,
        parse_mode="HTML"
    )

async def update_user_balance(user_id: int, amount_of_payout: float, msg2edit: types.Message, wallet_name: str):
    """
    Хз, зачем я вывел в отдельную функцию, но она просто делает проверку на балик и списывания денег с балика
    """
    
    
    balance = float(DB.get(user_id=user_id, data="balance", table=DB.users_table))
    if balance == 0:
        await msg2edit.edit_text(
            text="❌ Доступный баланс равен нулю"
        )
        return
    elif amount_of_payout > balance:
        await msg2edit.edit_text(
            text="❌ Сумма вывода больше, чем доступный баланс"
        )
        return
    
    else:
        new_balance = balance - amount_of_payout
        DB.update(user_id=user_id, column="balance", new_data=new_balance, table=DB.users_table)
        await msg2edit.edit_text(
            text="✅️ Заявка на выплату успешно создана! Ожидайте зачисления"
        )
        await send_payout_to_admin(user_id=user_id, amount_of_payout=amount_of_payout, wallet_name=wallet_name)



async def create_btns(
    btns_type: str,
    data_list: list,
    callback_data_main_btns: str,
    callback_data_nav_btns: str,
    back_callback: str,
    page: int = 0,
    main_btns_prefix: str = None,
    ids: list = None,
    
):
    """
    Алгоритм создания списка кнопок с промиками.

    btns_type = "stats", "delete", "edit" используется для информации промиков
    """
    buttons_per_page = 4
    inline_keyboard = []
    start_idx = page * buttons_per_page
    end_idx = start_idx + buttons_per_page
    promo_page = data_list[start_idx:end_idx]
    total_pages = (len(data_list) + buttons_per_page - 1) // buttons_per_page

    if -1 < page < total_pages:
        # Добавляем кнопки промокодов по 2 в ряд
        for i in range(0, len(promo_page), 2):
            row_buttons = []
            for j, code in enumerate(promo_page[i:i + 2]):
                # Определяем текущий индекс относительно data_list
                idx_in_data_list = start_idx + i + j
                # Присваиваем btns_type из ids, если оно определено и индекс не выходит за пределы
                current_btns_type = ids[idx_in_data_list] if ids and idx_in_data_list < len(ids) else btns_type
                row_buttons.append(types.InlineKeyboardButton(
                    text=main_btns_prefix + str(code),
                    callback_data=f"{callback_data_main_btns}{code}?{current_btns_type}"
                ))
            inline_keyboard.append(row_buttons)

        # Добавляем навигационные кнопки
        navigation_buttons = [
            types.InlineKeyboardButton(text="<", callback_data=f"{callback_data_nav_btns}{page - 1}?{btns_type}"),
            types.InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="pass"),
            types.InlineKeyboardButton(text=">", callback_data=f"{callback_data_nav_btns}{page + 1}?{btns_type}")
        ]
        inline_keyboard.append(navigation_buttons)
        inline_keyboard.append([types.InlineKeyboardButton(text="❄️", callback_data=back_callback)])
        # Создаем InlineKeyboardMarkup с параметром inline_keyboard
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    else:
        return False


async def create_promo_btns(user_id: int, btns_type: str, page: int = 0):
    
    promo_codes = DB.get_all_user_id(
        user_id=user_id,
        data="name",
        table=DB.promocodes
    )
    return await create_btns(btns_type=btns_type, 
                             page=page, 
                             data_list=promo_codes, 
                             callback_data_main_btns="promocode_", 
                             callback_data_nav_btns="promo_page_",
                             main_btns_prefix="",
                             back_callback="materials"
                             )


async def create_workers_btns(data_list: list, page: int = 0):
    return await create_btns(btns_type=None, 
                             page=page, 
                             data_list=data_list, 
                             callback_data_main_btns="worker_", 
                             callback_data_nav_btns="workers_page_", 
                             main_btns_prefix="👥",
                             back_callback="back_admin"
                             )

async def create_deposits_btns(data_list: list, ids: list, page: int = 0):
    return await create_btns(btns_type=None, 
                             page=page, 
                             data_list=data_list, 
                             callback_data_main_btns="deposit_", 
                             callback_data_nav_btns="deposits_page_", 
                             main_btns_prefix="💰",
                             ids=ids,
                             back_callback="back_admin"
                             )    

async def promo_view_stats(promo_name: str):
    api_result = await api.get_promo(promo_name)
    promo_data = api_result["data"]
    api_result_stats = await api.get_promo_stats(promo_name)
    countries = api_result_stats["data"]['countries']
    text = f"""
<b>📊 Статистика по промокоду - </b><code>{promo_data['name']}</code>
<blockquote><b>├💰Сумма промокода: {promo_data['amount']}$
├🎁Активаций: {promo_data['activations']}
├💸Депозитов: {promo_data['deposits']}$
├🎰Отыгрыш: {'Включен' if promo_data['shouldWager'] is True else 'Отключен'}
</b></blockquote><b>
📊Статистика по странам (Страна/Активаций/Депозитов/
Конверсия):</b>
"""    

    text+='<blockquote>'
    for country in countries:
        name = country_code_to_flag(country['name'])
        activations = country['activations']
        amount = country['amount']
        conversion = country['conversion']
        text += (f"<b>{name} {activations} / {amount}$ / {round(conversion, 2)}$</b>\n")
    text += '</blockquote>'
    return text


def country_code_to_flag(country_code):
    # Преобразуем код страны в верхний регистр и берем два первых символа
    code_points = [ord(char) - 0x41 + 0x1F1E6 for char in country_code.upper()]
    return chr(code_points[0]) + chr(code_points[1])


async def send_newDeposit(data: dict):
    today = datetime.now()

    cursor.execute(f"SELECT user_id FROM promocodes WHERE name = ?", (data['mammothPromo'], ))
    worker_id = cursor.fetchone()[0] #Получил user_id по промокоду
    
    worker_username = DB.get(user_id=worker_id, data="username", table=DB.users_table) #Username воркера получил
    worker_perc = DB.get(user_id=worker_id, data="percentage", table=DB.users_table) #Процент воркера получил
    
    cursor.execute(f"SELECT activation_count FROM promocodes WHERE name = ?", (data['mammothPromo'], ))
    old_promo_activations = cursor.fetchone()[0] # Получил колличество активаций промо по промокоду activation_count
    
    cursor.execute(f"SELECT deposit FROM promocodes WHERE name = ?", (data['mammothPromo'], ))
    old_promo_deposits = cursor.fetchone()[0] # хуй пойми че это ну наверное старое колличество депов на промике
    
    old_worker_balance = DB.get(user_id=worker_id, data="balance", table=DB.users_table)
    old_worker_all_time_balance = DB.get(user_id=worker_id, data="all_time_balance", table=DB.users_table)
    old_bot_all_time_balance = DB.get_without_user_id(data="all_time_balance", table=DB.bot_info)
    old_bot_all_promo_activations = DB.get_without_user_id(data="promo_activations", table=DB.bot_info)
    old_bot_deposits = DB.get_without_user_id(data="deposits", table=DB.bot_info)
    
    # Высчитываем новые значения
    new_bot_all_promo_activations = int(old_bot_all_promo_activations) + 1
    new_promo_activations = int(old_promo_activations) + 1
    new_promo_deposits = float(old_promo_deposits) + float(data['amountUsd'])
    new_worker_balance = float(old_worker_balance + (float(data['amountUsd'] * worker_perc) / 100))
    new_worker_all_time_balance = float(old_worker_all_time_balance) + (float(data['amountUsd'] * worker_perc) / 100)
    new_bot_all_time_balance = float(old_bot_all_time_balance) + float(data['amountUsd'])
    new_bot_deposits = int(old_bot_deposits) + 1

    # Округляем до 2 цифр после точки
    new_worker_balance = round(new_worker_balance, 2)
    new_promo_deposits = round(new_promo_deposits, 2)
    new_worker_all_time_balance = round(new_worker_all_time_balance, 2)
    new_bot_all_time_balance = round(new_bot_all_time_balance, 2)

    # Загружаем данные в БД
    DB.update(user_id=worker_id, column="balance", new_data=new_worker_balance, table=DB.users_table)
    DB.update(user_id=worker_id, column="all_time_balance", new_data=new_worker_all_time_balance, table=DB.users_table)
    
    DB.update_without_user_id(column="all_time_balance", new_data=new_bot_all_time_balance, table=DB.bot_info)
    DB.update_without_user_id(column="promo_activations", new_data=new_bot_all_promo_activations, table=DB.bot_info)
    DB.update_without_user_id(column="deposits", new_data=new_bot_deposits, table=DB.bot_info)
    
    
    cursor.execute(f"UPDATE promocodes SET activation_count = ? WHERE name = ?", (new_promo_activations, data['mammothPromo']))
    cursor.execute(f"UPDATE promocodes SET deposit = ? WHERE name = ?", (new_promo_deposits, data['mammothPromo']))
    conn.commit()

    # Сохраняем депозит в таблицу
    cursor.execute(
            'INSERT INTO deposits (worker_id, amount, mamonth_login, token, domain, date, hash, country, amountUSD)'
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (worker_id, float(data['amount']), str(data["mammothLogin"]), str(data["token"]), str(data["domain"]), today, str(data["txHash"]), str(data["mammothCountry"]), str(data["amountUsd"])))

    conn.commit()

    message_to_channel = f"""
<b>🔥 Хо-хо-хо! Новый депозит!
├🦋Никнейм воркера: <code>{worker_username if worker_username else '*****'}</code>
└❄️Сумма депозита: <code>{data['amountUsd']} $</code></b>
        """
    
    await bot.send_message(
        chat_id=GROUP_ID,
        text=message_to_channel,
        parse_mode='HTML'
    )
    
    message_to_user = f'''
<b>🔥 Хо-хо-хо! Вам пришел депозит!
├❄️Сумма: <code>{data['amountUsd']}$</code>
├❄️Почта мамонта: <code>{data['mammothLogin']}$</code>
├❄️Страна: <code>{data['mammothCountry']}$</code>
└🔐Домен: <code>{data['domain']}</code></b>
'''
    await bot.send_message(
        chat_id=worker_id,
        text=message_to_user,
        parse_mode='HTML'
    )
    
def create_top_list():
    users_list = []
    users = DB.get_all(data="user_id", table=DB.users_table)
    text = '''
🥇 Топ воркеров

'''
    for i, user_id in enumerate(users, start=1):
        worker_username = DB.get(user_id=user_id, data="tg_username", table=DB.users_table)
        worker_firstname = DB.get(user_id=user_id, data="tg_firstname", table=DB.users_table)
        worker_balance = DB.get(user_id=user_id, data="all_time_balance", table=DB.users_table)
        users_list.append([user_id, worker_balance, worker_firstname, worker_username])

    users_list.sort(key=lambda x: x[1], reverse=True)
    
    for i, user in enumerate(users_list, start=1):
        if i == 11: break
            
        if i == 1:
            text += f"🥇‍ Воркер: {user[2]} (@{user[3]}) / id{user[0]}\nЗа все время: {user[1]}$\n\n"
        elif i == 2:
            text += f"🥈‍ Воркер: {user[2]} (@{user[3]}) / id{user[0]}\nЗа все время: {user[1]}$\n\n"
        elif i == 3:
            text += f"🥉 Воркер: {user[2]} (@{user[3]}) / id{user[0]}\nЗа все время: {user[1]}$\n\n"
        else:
            text += f"👨 Воркер: {user[2]} (@{user[3]}) / id{user[0]}\nЗа все время: {user[1]}$\n\n"
    
    
    return text


async def create_worker_profile(worker_id: int):
    worker_name = DB.get(user_id=worker_id, data="tg_firstname", table=DB.users_table)
    worker_username = DB.get(user_id=worker_id, data="tg_username", table=DB.users_table)
    text = f"👥 Воркер {worker_id} ({worker_name}/@{worker_username})"
    worker_btns = [
        [types.InlineKeyboardButton(text="⛏️ Забанить // Разбанить", callback_data=f"ban/unban_{worker_id}")],
        [types.InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"changeBalance_{worker_id}")],
        [types.InlineKeyboardButton(text="🤝 Процент выплат", callback_data=f"show_percentage_{worker_id}"), types.InlineKeyboardButton(text="💳  Кошельки", callback_data=f"show_wallets_{worker_id}")],
        [types.InlineKeyboardButton(text="❄️", callback_data=f"workers_page_0?None")]
    ]
    return text, worker_btns



class OutputInterceptor(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout


async def read_subprocess_output(stream):
    while True:
        try:
            line = await stream.readline()
            if not line:
                break
            logger = create_logger("socket_handler")
            logger.log(level=logging.INFO, msg=f'{line.decode().strip()}')
        except Exception:
            continue