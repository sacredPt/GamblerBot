from datetime import datetime
import time
from config import *
import utils
from db import DB, cursor, conn
import api
import handlers.cmd_handler as cmd_handler
from log import create_logger
logger = create_logger(__name__)
import main
import json
from aiogram.types import MessageEntity
from aiogram import types

@dp.callback_query(F.data == F.data)
async def inline_handler(call: types.CallbackQuery, state: FSMContext):
    """
    Единый handler inline кнопок
    """
    logger.info(f"Received inline callback \"{str(call.data)}\" from @{call.from_user.username}")
    # Обновление в БД username и firstname юзера для достоверности информации
    DB.update(user_id=call.from_user.id, column="tg_firstname", new_data=call.from_user.first_name, table=DB.users_table)
    DB.update(user_id=call.from_user.id, column="tg_username", new_data=call.from_user.username, table=DB.users_table)
    _is_banned = DB.get(user_id=call.from_user.id, data="_is_banned", table=DB.users_table)
    if str(call.from_user.id) in ADMIN_IDS or _is_banned == "False":
        if "user_request_" in str(call.data):
            admin_solution = str(call.data).split("_")[2].split("?")[0]
            target_user_id = str(call.data).split("?")[1]
            target_username = DB.get(user_id=target_user_id, data='tg_username', table=DB.unconfirmed_users_table)
            user = DB.get(user_id=target_user_id, data="user_id", table=DB.users_table)
            print(user)
            if not user:
                if admin_solution == 'accept':
                    DB.update(user_id=target_user_id, column="state", new_data="confirmed", table=DB.unconfirmed_users_table)
                    DB.insert(user_id=target_user_id, tg_username=target_username, tg_firstname="None")
                    await call.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="✅ Принята!", callback_data="pass")]]))
                    text='''
✨ Поздравляем! Ваша заявка была <b>одобрена!</b>
⌨️ Для того чтобы воспользоваться ботом - используйте клавиатуру ниже.

❄️ Приятной вам работы в команде <b>Elysium</b>!
'''
                    msg = await bot.send_message(
                        text="✅ Заявка была принята, успешной работы! Если у вас не отобразилось меню бота пропишите /start",
                        chat_id=target_user_id,
                    )
                    await cmd_handler.start(msg=msg, state=state, user_id=target_user_id)

                elif admin_solution == "decline":
                    DB.update(user_id=target_user_id, column="state", new_data="unconfirmed", table=DB.unconfirmed_users_table)
                    await call.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Отклонена!", callback_data="pass")]]))
                    await bot.send_message(
                        text=f"❌ Заявка была отклонена, для уточнения причины свяжитесь с администрацией - {config['admin_username']}",
                        chat_id=target_user_id
                    )
            else:
                btns = [[
                    types.InlineKeyboardButton(text="Заявка уже рассмотрена", callback_data="pass")
                ]]
                await call.message.edit_reply_markup(
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns)
                )
        # elif call.data == "user_profile":
        #     await utils.show_user_profile(call)
        
        elif call.data == "change_username":
            await call.message.edit_text(
                text="⭐️ Введите новый ник, который будет отображаться в отстуке:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
            )
            await state.set_state(States.change_username)
        
        elif call.data == "link_wallet":
            link_wallet_btns = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="BTC", callback_data="link_wallet_BTC"), types.InlineKeyboardButton(text="USDT", callback_data="link_wallet_USDT")],
                [types.InlineKeyboardButton(text="❄️", callback_data="user_profile")]
            ])
            await call.message.edit_text(
                text="💳 Выберите какой кошелек вы хотите привязать/изменить",
                reply_markup=link_wallet_btns
            )
        
        elif call.data == "promo_setts":
            
            promocodes = DB.get_all_user_id(
                user_id=call.from_user.id,
                data="name",
                table=DB.promocodes
            )
            inline_keyboard = []
            for code in promocodes:
                inline_keyboard.append(
                    [
                        types.InlineKeyboardButton(text=str(code), callback_data=f"statspromo_{code}")
                    ]
                )
            
            inline_keyboard.append(
                    [
                        types.InlineKeyboardButton(text='➕ Создать промокод', callback_data=f"create_promo")
                    ] 
                )
            inline_keyboard.append(
                    [
                        types.InlineKeyboardButton(text="❄️", callback_data="back_main")
                    ]  
                )
            
            
            try:
                await call.message.edit_text('⚙️ Настройки')
            except:
                a=2
            await call.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard))
        
        elif call.data.startswith('statspromo_'):
            
            promocode = call.data.split('_')[1]
            promo_view_text = await utils.promo_view_stats(promocode)
            
            inline_keyboard = [
                [
                    types.InlineKeyboardButton(text="♻️ Обновить", callback_data=f"updatepromostats_{promocode}"),
                    types.InlineKeyboardButton(text="⚙️ Редактировать", callback_data=f"editpromo_{promocode}"),
                    types.InlineKeyboardButton(text="🗑 Удалить", callback_data=f"deletecode_{promocode}")
                    
                ],
                [
                    types.InlineKeyboardButton(text="❄️", callback_data="promo_setts")
                ]
            ]
            
            await call.message.edit_text(
                text=promo_view_text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                parse_mode='HTML'
            )
        
        elif call.data.startswith('updatepromostats_'):
            promocode = call.data.split('_')[1]
            try:
                promo_view_text = await utils.promo_view_stats(promocode)
                inline_keyboard = [
                    [
                        types.InlineKeyboardButton(text="♻️ Обновить промокод", callback_data=f"updatepromostats_{promocode}"),
                        types.InlineKeyboardButton(text="✍️ Редактировать промокод", callback_data=f"editpromo_{promocode}"),
                        types.InlineKeyboardButton(text="❌ Удалить промокод", callback_data=f"deletecode_{promocode}")
                    ],
                    [
                        types.InlineKeyboardButton(text="❄️", callback_data="promo_setts")
                    ]
                ]
                
                await call.message.edit_text(
                    text=promo_view_text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                    parse_mode='HTML'
                )
            except:
                 await call.answer("🔴 Статистика не изменилась!", show_alert=True)
        
        elif call.data.startswith('deletecode_'):
            promocode = call.data.split('_')[1]
            text = f'⁉️ Вы уверены, что хотите удалить промокод {promocode}?'
            btns = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ Отменить", callback_data=f"promocodeDelete_decline?{promocode}"), types.InlineKeyboardButton(text="✅ Удалить", callback_data=f"promocodeDelete_accept?{promocode}")]
            ])
            await call.message.edit_text(
                text=text,
                reply_markup=btns
            )
        
        elif call.data.startswith('editpromo_'):
            promocode = call.data.split('_')[1]
            btns = types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="💰 Сумма", callback_data=f"promocodeEdit_amount?{promocode}"),
                        types.InlineKeyboardButton(text="🎰 Отыгрыш", callback_data=f"promocodeEdit_ubt?{promocode}")
                    ],
                    [
                        types.InlineKeyboardButton(text="❄️", callback_data=f"statspromo_{promocode}")
                    ]
                    
                ])
            cursor.execute(f"SELECT amount, ubt FROM promocodes WHERE name = ?", (promocode, ))
            result = cursor.fetchall()[0]
            promo_amount = result[0]
            promo_ubt = result[1]
            text = f'''<b>
📊 Статистика по промокоду "<code>{promocode}</code>":
├💰Сумма промокода: <code>{promo_amount}</code>$
└🎰Отыгрыш: <code>{"включен" if promo_ubt == "enable" else "выключен"}</code></b>

            ''' 
            await call.message.edit_text(
                text=text,
                reply_markup=btns,
                parse_mode='HTML'
            )
            
        elif "link_wallet_" in str(call.data):
            
            wallet_name = str(call.data).split("_")[2]
            print(wallet_name)
            if wallet_name == 'USDT':
                await call.message.edit_text(
                    text=f"<b>💳 Введите новый адрес вашего USDT TRC20 кошелька</b>",
                    parse_mode='HTML'
                )
            else:
                await call.message.edit_text(
                    text=f"<b>💳 Введите новый адрес вашего BTC кошелька</b>", 
                    parse_mode='HTML'
                )
            
            await state.set_state(States.link_wallet)
            await state.update_data(wallet_name=wallet_name)

        elif call.data == "payout":
            payout_btns = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="BTC", callback_data="payout_BTC"), types.InlineKeyboardButton(text="USDT", callback_data="payout_USDT")],
                [types.InlineKeyboardButton(text="❄️", callback_data="back_main")]
            ])
            await call.message.edit_text(
                text="💸 На какой кошелек вы хотите заказать выплату?",
                reply_markup=payout_btns
            )

        elif str(call.data).startswith("all_payout_"):
            await state.clear()
            balance = DB.get(user_id=call.from_user.id, data="balance", table=DB.users_table)
            await utils.update_user_balance(
                user_id=call.from_user.id,
                amount_of_payout=balance,
                msg2edit=call.message,
                wallet_name=str(call.data).split("_")[2]
            )

        elif str(call.data).startswith("payout_request_accept?"):
            user_id = str(call.data).split("?")[1]
            await call.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="✅ Выплачена!", callback_data="pass")]])
                )
            await bot.send_message(
                chat_id=user_id,
                text="✅ Выплата совершена, проверьте кошелек"
            )

        elif str(call.data).startswith("payout_request_decline?"):
            user_id = str(call.data).split("?")[1]
            await call.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Отклонена!", callback_data="pass")]])
                )
            await bot.send_message(
                chat_id=user_id,
                text="❌ Выплата отклонена, деньги вернулись на баланс"
            )
            msg_text_list = str(call.message.text).splitlines()
            amount_of_payout = msg_text_list[2].split(":")[1].replace("$", "").replace(" ", "")
            user_id = msg_text_list[1].split("/")[1].replace(" ", "")
            balance = DB.get(user_id=user_id, data="balance", table=DB.users_table)
            DB.update(user_id=user_id, column="balance", new_data=float(balance) + float(amount_of_payout), table=DB.users_table)


        elif str(call.data).startswith("payout_"):
            wallet_data = DB.get(user_id=call.from_user.id, data=f"{str(call.data).lower().split('_')[1]}_wallet", table=DB.users_table)
            if wallet_data is None:
                await call.message.edit_text(
                    text=f"❌ Укажите {str(call.data).split('_')[1]} кошелек для выплаты"
                )
                return
            print(wallet_data)
            text = f'''
<b>📝 Введите сумму которую вы хотите вывести:</b>

<blockquote><b>💰Доступно для вывода: {DB.get(user_id=call.from_user.id, data="balance", table=DB.users_table)}$
👛Кошелек для вывода: {wallet_data}</b></blockquote>
                '''
            payout_btns = types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="💸 Вывести все", callback_data=f"all_payout_{str(call.data).split('_')[1]}"),
                    types.InlineKeyboardButton(text="❗️ Отменить заявку", callback_data="cancel_payout")
                ],
                [
                    types.InlineKeyboardButton(text="❄️", callback_data="back_main")
                ],
            ])

            await call.message.edit_text(
                text=text,
                reply_markup=payout_btns,
                parse_mode='HTML'
            )
            await state.set_state(States.payout_amount)
            await state.update_data(msg2edit=call.message)
            await state.update_data(wallet=str(call.data).split("_")[1])
        
        elif call.data == "cancel_payout":
            start_btns = types.ReplyKeyboardMarkup(keyboard=[
                    [
                        types.KeyboardButton(text="☃️ Профиль"), types.KeyboardButton(text="🌏 Актуальные домены")
                    ],
                    [
                        types.KeyboardButton(text="⚙️ Настройки"), types.KeyboardButton(text="📄 Информация")
                    ]
            ], resize_keyboard=True)
            await state.clear()
            await cmd_handler.start(
                msg=call.message,                       
                state=state, 
                user_id=call.from_user.id, 
                edit_msg=True
            )

        elif str(call.data).startswith("promo_ubt_"):
            print('DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD')
            promo_ubt_state = str(call.data).split("_")[2].split("?")[0]
            creator_user_id = str(call.data).split("?")[1].split("_")[0]
            name = str(str(call.data).split("?")[1].split("_")[1]).lower()
            amount = str(call.data).split("?")[1].split("_")[2]
            DB.insert_promo(user_id=creator_user_id, name=name, ubt=promo_ubt_state, amount=amount)
            api_result = await api.create_promo(
                data={
                    'name': name,
                    'amount': amount,
                    'shouldWager': True if promo_ubt_state == "enable" else False,
                }
            )
            text=f'''
<b>💎Ваш промокод был успешно создан!

📄Информация о вашем промокоде</b>
<blockquote><b>🎟Ваш промокод:</b> {name}
<b>💸Сумма бонуса мамонту при регистрации:</b> {amount}$
<b>🎰Отыгрыш промокода:</b> {'Включен.' if promo_ubt_state == "enable" else 'Выключен.'}
</blockquote>


'''
            if api_result["success"] is True:
                await call.message.edit_text(
                    text=text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="❄️", callback_data=f"promo_setts")
                        ]
                    ]),
                    parse_mode='HTML'
                )

        elif call.data == "create_promo":
            await call.message.edit_text(
                text="<b>💰 Введите сумму которую получит мамонт при вводе промокода (указывать в $):</b>",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="❄️", callback_data="promo_setts")
                    ]
                ]),
                parse_mode='HTML'
            )
            await state.set_state(States.create_promo_amount)

        elif call.data == "stats_promo":
            count_of_promocodes = DB.get_all_user_id(
                user_id=call.from_user.id,
                data="name",
                table=DB.promocodes
            )
            if len(count_of_promocodes) == 0:
                await call.answer(
                    text="❌ У вас нет промокодов",
                    show_alert=True
                )
            else:
                btns = await utils.create_promo_btns(user_id=call.from_user.id, btns_type="stats")
                text = '''
👀 Выберите промокод для статистики
                    '''
                await call.message.edit_text(
                    text=text,
                    reply_markup=btns
                )

        elif call.data == "delete_promo":
            count_of_promocodes = DB.get_all_user_id(
                user_id=call.from_user.id,
                data="name",
                table=DB.promocodes
            )
            if len(count_of_promocodes) == 0:
                await call.answer(
                    text="❌ У вас нет промокодов",
                    show_alert=True
                )
            else:
                btns = await utils.create_promo_btns(user_id=call.from_user.id, btns_type="delete")
                text = '👀 Выберите, какой промокод хотите удалить'
                await call.message.edit_text(
                    text=text,
                    reply_markup=btns
                )
            
        elif call.data == "edit_promo":
            count_of_promocodes = DB.get_all_user_id(
                user_id=call.from_user.id,
                data="name",
                table=DB.promocodes
            )
            if len(count_of_promocodes) == 0:
                await call.answer(
                    text="❌ У вас нет промокодов",
                    show_alert=True
                )
            else:
                btns = await utils.create_promo_btns(user_id=call.from_user.id, btns_type="edit")
                text = '👀 Выберите промокод для редактирования'        
                await call.message.edit_text(
                    text=text,
                    reply_markup=btns
                )

        elif str(call.data).startswith("promocode_"):
            promo_name = str(call.data).split("_")[1].split("?")[0]
            btn_type = str(call.data).split("?")[1]
            if btn_type == "stats":
                promo_view_text = await utils.promo_view_stats(promo_name)
                await call.message.edit_text(
                    text=promo_view_text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]]),
                    parse_mode='HTML'
                )
            elif btn_type == "delete":
                text = f'⁉️ Вы уверены, что хотите удалить промокод {promo_name}?'
                btns = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="❌ Отменить", callback_data=f"promocodeDelete_decline?{promo_name}"), types.InlineKeyboardButton(text="✅ Удалить", callback_data=f"promocodeDelete_accept?{promo_name}")]
                ])
                await call.message.edit_text(
                    text=text,
                    reply_markup=btns
                )
            elif btn_type == "edit":
                btns = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="Сумма", callback_data=f"promocodeEdit_amount?{promo_name}"), types.InlineKeyboardButton(text="Отыгрыш", callback_data=f"promocodeEdit_ubt?{promo_name}")]
                ])
                cursor.execute(f"SELECT amount, ubt FROM promocodes WHERE name = ?", (promo_name, ))
                result = cursor.fetchall()[0]
                promo_amount = result[0]
                promo_ubt = result[1]
                text = f'''
✍️ Редактировать промокод
👀 Промокод: {promo_name}
💵 Сумма промокода: {promo_amount}
🎰 Отыгрыш промокода: {"включен" if promo_ubt == "enable" else "выключен"}
                ''' 
                await call.message.edit_text(
                    text=text,
                    reply_markup=btns
                )

        elif str(call.data).startswith("promocodeEdit_"):
            edit_type = str(call.data).split("_")[1].split("?")[0]
            promo_name = str(call.data).split("?")[1]
            if edit_type == "amount":
                text = f"💵 Введите новую сумму промокода {promo_name}:"
                await call.message.edit_text(
                    text=text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
                )
                await state.set_state(States.edit_promo_amount)
                await state.update_data(promo_name=promo_name)
            elif edit_type == "ubt":
                cursor.execute('SELECT ubt FROM promocodes WHERE name = ?', (promo_name, ))
                promo_ubt = cursor.fetchone()[0]
                text = f"🎰 Отыгрыш промокода {promo_name}: {'включен' if promo_ubt == 'enable' else 'отключен'}"
                promo_edit_btns = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="✅ Отключен", callback_data=f"promocodeEdit?ubt_disable_{promo_name}"), types.InlineKeyboardButton(text="❌ Включен", callback_data=f"promocodeEdit?ubt_enable_{promo_name}")]
                ])
                await call.message.edit_text(
                    text=text,
                    reply_markup=promo_edit_btns
                )
        
        elif str(call.data).startswith("promocodeEdit?ubt_"):
            edit_state = str(call.data).split("_")[1]
            promo_name = str(call.data).split("_")[2]
            promo = await api.get_promo(promo_name)
            promo_amount = promo["data"]["amount"]

            try:
                cursor.execute("UPDATE promocodes SET ubt = ? WHERE name = ?", (edit_state, promo_name))
                conn.commit()
                api_result = await api.edit_promo({
                    'name': promo_name,
                    'amount': promo_amount,
                    'shouldWager': True if edit_state == "enable" else False
                })
                if api_result["success"] is True:
                    await call.message.edit_text(
                        text="✅️ Промокод успешно отредактирован!",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
                    )
                else:
                    raise Exception
            except Exception:
                await call.message.edit_text(
                    text="❌ При редактировании промокода произошла ошибка!",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
                )

        elif str(call.data).startswith("promocodeDelete_"):
            delete_state = str(call.data).split("_")[1].split("?")[0]
            promo_name = str(call.data).split("?")[1]
            if delete_state == "accept":
                try:
                    cursor.execute(f"DELETE from promocodes where name = ?", (promo_name,))
                    conn.commit()
                    api_result = await api.delete_promo(promo_name)
                    if api_result["success"] is True:
                        await call.message.edit_text(
                            text="<b>✅️ Промокод успешно удален!</b>",
                            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    types.InlineKeyboardButton(text="❄️", callback_data=f"promo_setts")
                                ]
                            ]),
                            parse_mode='HTML'
                        )
                    else:
                        raise Exception
                except Exception:
                    await call.message.edit_text(
                        text="<b>❌ При удалении промокода произошла ошибка!</b>",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [
                                types.InlineKeyboardButton(text="❄️", callback_data=f"promo_setts")
                            ]
                        ]),
                        parse_mode='HTML'
                    )


        elif str(call.data).startswith("promo_page_"):
            page = int(str(call.data).split("_")[2].split("?")[0])
            btns_type = str(call.data).split("?")[1]
            btns = await utils.create_promo_btns(
                user_id=call.from_user.id, 
                btns_type=btns_type, 
                page=page
            )
            if btns is not False:
                await call.message.edit_reply_markup(
                    reply_markup=btns
                )
            else:
                await call.answer()
                return
        
        elif str(call.data).startswith("workers_page_"):
            page = int(str(call.data).split("_")[2].split("?")[0])
            workers = DB.get_all(data="user_id", table=DB.users_table)
            btns = await utils.create_workers_btns(data_list=workers, page=page)
            if btns is not False:
                await call.message.edit_reply_markup(
                    reply_markup=btns
                )
            else:
                await call.answer()
                return

        elif str(call.data).startswith("worker_"):
            worker_id = str(call.data).split("_")[1].split("?")[0]
            text, worker_btns = await utils.create_worker_profile(worker_id)
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=worker_btns)
            )

        elif str(call.data).startswith("ban/unban_"):
            worker_id = str(call.data).split("_")[1]
            ban_state = DB.get(user_id=worker_id, data="_is_banned", table=DB.users_table)
            if ban_state:
                ban_state = f'{"True" if ban_state == "False" else "False"}'
                result = DB.update(user_id=worker_id, column="_is_banned", new_data=ban_state, table=DB.users_table)
                if result:
                    await call.answer("Пользователь успешно " + ("заблокирован" if ban_state == 'True' else "разблокирован"))
                else:
                    print(2)

        elif str(call.data).startswith("changeBalance_"):
            worker_id = str(call.data).split("_")[1]
            worker_name = DB.get(user_id=worker_id, data="tg_firstname", table=DB.users_table)
            worker_username = DB.get(user_id=worker_id, data="tg_username", table=DB.users_table)
            worker_balance = DB.get(user_id=worker_id, data="balance", table=DB.users_table)
            await state.set_state(States.user_input_new_balance)
            await state.update_data(worker_id=worker_id)
            text = f"""
👥 Воркер {worker_id} ({worker_name}/@{worker_username})

Баланс: {worker_balance}
Введите новый баланс:"""
            await call.message.edit_text(
                text=text,
            )
        
        elif str(call.data).startswith("show_wallets_"):
            worker_id = str(call.data).split("_")[2]
            worker_name = DB.get(user_id=worker_id, data="tg_firstname", table=DB.users_table)
            worker_username = DB.get(user_id=worker_id, data="tg_username", table=DB.users_table)
            worker_btc_wallet = DB.get(user_id=worker_id, data="btc_wallet", table=DB.users_table)
            worker_usdt_wallet = DB.get(user_id=worker_id, data="usdt_wallet", table=DB.users_table)
            text = f'''
👥 Воркер {worker_id} ({worker_name}/@{worker_username}) 
👛 Привязанные кошельки:
└ BTC: {worker_btc_wallet}
└ USDT TRC-20: {worker_usdt_wallet}
                '''
            btns = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❄️", callback_data=f"worker_{worker_id}")]
            ])
            await call.message.edit_text(
                text=text,
                reply_markup=btns
            )

        elif str(call.data).startswith("show_percentage_"):
            worker_id = str(call.data).split("_")[2]
            worker_name = DB.get(user_id=worker_id, data="tg_firstname", table=DB.users_table)
            worker_username = DB.get(user_id=worker_id, data="tg_username", table=DB.users_table)
            worker_perc = DB.get(user_id=worker_id, data="percentage", table=DB.users_table)
            text = f'''
👥 Воркер {worker_id} ({worker_name}/@{worker_username}) 
🤝 Процент выплат - {worker_perc}%
✍️ Введите новый процент воркера:
                '''
            btns = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data=f"worker_{worker_id}")]])
            await call.message.edit_text(
                text=text,
                reply_markup=btns
            )
            await state.set_state(States.edit_worker_perc)
            await state.update_data(worker_id=worker_id)
        
            
        elif call.data == "admin_info":
            await state.clear()
            await call.message.edit_text(text="Введите текст в кнопке “Информация”:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="back_admin")]]))
            await state.set_state(States.edit_info)

        elif call.data == "admin_url":
            await state.clear()
            await call.message.edit_text(text="Введите актуальный домен (можно несколько):", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="back_admin")]]))
            await state.set_state(States.edit_url)

        elif call.data == "admin_workers":
            await state.clear()
            workers = DB.get_all(data="user_id", table=DB.users_table)
            workers_btns = await utils.create_workers_btns(workers)
            await call.message.edit_text(
                text="👀 Выберите воркера или напишите /user + тег/айди",
                reply_markup=workers_btns
            )

        elif call.data == "admin_topWorkers":
            text = utils.create_top_list()
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="back_admin")]])
            )

        elif call.data == "admin_stats":
            data = await api.get_profile_stats()
            profile_data = data["data"]
            all_time_balance = profile_data["depositsAll"]
            all_users = profile_data["users"]
            all_time_promo_act = profile_data["promoActivations"]
            verif_users = profile_data["verified"]
            multi_deposits = profile_data["multiDeps"]
            conversion = profile_data["conversion"]
            text = f'''
⌛️ Статистика за все время со всех доменов:

💰 Доход: {all_time_balance}$
👥 Пользователей: {all_users}
🎟 Активаций промокодов: {all_time_promo_act}  
🛂 Прошли верификацию: {verif_users}
💳 Повторных депозитов: {multi_deposits}
💸 Конверсия рег./депов: {round(conversion, 3)}$
                '''
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="back_admin")]])
            )

        elif call.data == "admin_msg":
            text = '''
💬 Введите сообщение для рассылки:
                '''
            btns = [
                [types.InlineKeyboardButton(text="❌ Отменить", callback_data="back_admin")]
            ]
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns)
            )
            await state.set_state(States.admin_ad)
            
        
        elif str(call.data).startswith("adminMsg_"):
            msg_state = str(call.data).split("_")[1]
            if msg_state == "accept":
                start_timestamp = time.time()
                await call.message.edit_text(
                    text="✅ Рассылка запущена!",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
                )
                text = call.message.text
                users = DB.get_all("user_id", DB.users_table)
                tasks = []
                async def send_msg_to_user(user_id):
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=text,
                            entities=call.message.entities
                        )
                        return True
                    except Exception:
                        return False
                    
                tasks.extend([send_msg_to_user(user_id) for user_id in users])
                results = await asyncio.gather(*tasks)    
                success = results.count(True)
                errors = results.count(False)
                admin_text = f"""
✅️ Рассылка завершена успешно!
Отправлено: {success}
Не отправлено: {errors}
Затрачено времени: {datetime.fromtimestamp(time.time() - start_timestamp).strftime("%M мин %S сек")}
                """
                await call.message.answer(
                    text=admin_text
                )
            else:
                await call.message.edit_text(
                    text="❌ Рассылка отменена!",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
                )
                return
        
        elif call.data == "admin_settings":
            await call.message.edit_text(
                text="⚙️ Настройки",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🤝 Проценты выплат", callback_data="admin_settings_percentage")], 
                                                                        [types.InlineKeyboardButton(text="❄️", callback_data="back_admin")]
                                                                        ])
            )

        elif call.data == "admin_settings_percentage":
            btns = [
                [types.InlineKeyboardButton(text="Изменить у всех", callback_data="admin_change_perc?all")],
                [types.InlineKeyboardButton(text="Изменить у всех, кроме тех, кому меняли вручную", callback_data="admin_change_perc?manual")],
                [types.InlineKeyboardButton(text="❄️", callback_data="admin_settings")]
            ]
            await call.message.edit_text(
                text="🤝 Проценты выплат",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns)
            )
        
        elif str(call.data).startswith("admin_change_perc?"):
            perc_state = str(call.data).split("?")[1]
            if perc_state == "all":
                text = '''
👥 Изменить у всех

Введите процент выплат, который изменится у всех трафферов (просто число, например 50):
                        '''
                await state.set_state(States.admin_perc_change_all)
                await call.message.edit_text(
                    text=text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="admin_settings_percentage")]])
                )
            elif perc_state == "manual":
                text = '''
👥 Изменить у всех, кроме тех, кому меняли вручную

Введите процент выплат, который изменится у всех трафферов, кроме тех, кому меняли вручную (просто число, например 50):
                    '''
                await state.set_state(States.admin_perc_change_manual)
                await call.message.edit_text(
                    text=text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="admin_settings_percentage")]])
                )

        elif call.data == "admin_deposits":
            cursor.execute(f"SELECT id, amountUSD FROM {DB.deposits}")
            fetch = cursor.fetchall()
            deposits = []
            ids = []
            for item in fetch:
                deposits.append(item[1])
                ids.append(item[0])
            else:
                if deposits:
                    btns = await utils.create_deposits_btns(data_list=deposits, ids=ids)
                    text = '''
👀 Выберите депозит для просмотра
                        '''
                    await call.message.edit_text(
                        text=text,
                        reply_markup=btns
                    )
                else:
                    await call.message.edit_text(
                        text="❌ Депозиты не найдены",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="back_admin")]])
                    )
                    

        elif str(call.data).startswith("deposits_page_"):
            page = int(str(call.data).split("_")[2].split("?")[0])
            cursor.execute(f"SELECT id, amountUSD FROM {DB.deposits}")
            fetch = cursor.fetchall()
            deposits = []
            ids = []
            for item in fetch:
                deposits.append(item[1])
                ids.append(item[0])
            btns = await utils.create_deposits_btns(data_list=deposits, page=page, ids=ids)
            if btns is not False:
                await call.message.edit_reply_markup(
                    reply_markup=btns
                )
            else:
                await call.answer()
                return        

        elif str(call.data).startswith("deposit_"):
            deposit_id = str(call.data).split("?")[1]
            cursor.execute(f"SELECT * FROM {DB.deposits} WHERE id = ?", (deposit_id, ))
            deposit_data = cursor.fetchall()[0]
            worker_name = DB.get(user_id=deposit_data[1], data="tg_firstname", table=DB.users_table)
            worker_username = DB.get(user_id=deposit_data[1], data="tg_username", table=DB.users_table)
            text = f'''
👀 Депозит {deposit_data[3]} $
👨‍ Воркер: {worker_name} (@{worker_username}) / {deposit_data[1]} 
🦣 Логин мамонта: {deposit_data[4]}
💎 Монета: {deposit_data[5]}
🔗 Домен: {deposit_data[6]}
🗓 Дата: {deposit_data[7]} 
⛓️ Хеш: {deposit_data[8]}
                '''
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[]])
            )

        elif str(call.data).startswith("back_"):
            menu = str(call.data).split("_")[1]
            await state.clear()
            if menu == "main": await cmd_handler.start(
                msg=call.message,                       
                state=state, 
                user_id=call.from_user.id, 
                edit_msg=True
            )
            
            elif menu == "admin": await cmd_handler.admin(
                msg=call.message,
                state=state,
                user_id=call.from_user.id,
                edit_msg=True
            )
        
        elif call.data == "admin":
            await state.clear()
            await cmd_handler.admin(msg=call.message, state=state, user_id=call.from_user.id)


        elif call.data == "pass":
            await call.answer()
            return

        else:
            await call.answer("Недоступно...")
    
    else:
        if call.data == 'send_req_zz':
            await call.message.edit_text(
                text="✍🏻 Опишите ваш опыт работы:"
            )
            await state.set_state(States.start_input)
        else:
            await call.answer("Вы были заблокированы!", show_alert=True)