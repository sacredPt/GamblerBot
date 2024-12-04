import json

from api import get_promo
from config import *
import utils
from db import DB, cursor, conn
import api
from log import create_logger
import handlers.cmd_handler as cmd_handler
logger = create_logger(__name__)


@dp.message(States.start_input)
async def start_input(msg: types.Message, state: FSMContext):
    if msg.text:
        await state.clear()
        await msg.delete()
        await msg.answer("✍🏻 Укажите ссылку на ваш аккаунт на форуме(lolz.live):")
        await state.set_state(States.start_sec_input)
        await state.update_data(exp=msg.text)


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> MEMBER))
async def bot_added_as_member(event: ChatMemberUpdated, state: FSMContext):
    await event.answer(f"ID: <code>{event.chat.id}</code>", parse_mode='HTML')

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR))
async def bot_added_as_member(event: ChatMemberUpdated, state: FSMContext):
    await event.answer(f"ID: <code>{event.chat.id}</code>", parse_mode='HTML')

@dp.message(States.start_sec_input)
async def start_sec_input(msg: types.Message, state: FSMContext):
    if msg.text:
        await msg.delete()
        state_data = await state.get_data()
        exp = state_data["exp"]
        await state.clear()
        try:
            forum_url = msg.text
            DB.insert_new_user(user_id=msg.from_user.id, tg_username=msg.from_user.username, forum_url=forum_url, exp=exp)
            await utils.send_request_to_admin(msg, forum_url, exp)
            text='''
❄️ Ваша заявка успешно отправлена!

✨ В ближайшее время администраторы рассмотрят Вашу заявку - ожидайте!

🎄 С уважением команда проекта Elysium!

<span class="tg-spoiler">🕘 Среднее время ответа на заявки: 20 минут.</span>
'''
            await msg.answer(text, parse_mode='HTML')
        except Exception as e:
            logger.error(e)
            DB.delete(user_id=msg.from_user.id, table=DB.unconfirmed_users_table)
            await msg.answer("⛔️ Ваша заявка не была отправлена! Попробуйте еще раз")
        

@dp.message(States.change_username)
async def change_username(msg: types.Message, state: FSMContext):
    if msg.text:
        await state.clear()
        new_username = msg.text
        result = DB.update(user_id=msg.from_user.id, column="username", new_data=new_username, table=DB.users_table)
        if result is True:
            msg2edit = await msg.answer("✅️ Новый ник успешно сохранен!")
            await asyncio.sleep(2)
            await utils.show_user_profile(msg=msg, msg2edit=msg2edit)


@dp.message(States.link_wallet)
async def link_wallet(msg: types.Message, state: FSMContext):
    if msg.text:
       
        state_data = await state.get_data()
        
        await bot.delete_message(
            msg.from_user.id,
            int(state_data["old_msg_id"])
        )
        wallet_name = str(state_data["wallet_name"]).lower()
        await state.clear()
        result = DB.update(user_id=msg.from_user.id, column=f"{wallet_name}_wallet", new_data=msg.text, table=DB.users_table)
        
        if result is True:
            if wallet_name == 'usdt':
                await msg.answer(
                    text=f"<b>💎 Новый адрес USDT TRC20 кошелька сохранен!</b>",
                    parse_mode='HTML',
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="❄️", callback_data="back_delete")
                        ]
                    ]),
                )
                await cmd_handler.start(
                    msg=msg,                       
                    state=state, 
                    user_id=msg.from_user.id, 
                    edit_msg=True
                )
            else:
                await msg.answer(
                    text=f"<b>💎 Новый адрес BTC кошелька сохранен!</b>",
                    parse_mode='HTML',
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="❄️", callback_data="back_delete")
                        ]
                    ]),
                )
        else:
            await msg.answer(
                text=f"⛔️ Произошла ошибка при сохранении нового {wallet_name.upper()} кошелька!",
            )


@dp.message(States.payout_amount)
async def payout_amount(msg: types.Message, state: FSMContext):
    if (msg.text).isdigit():
        state_data = await state.get_data()
        await state.clear()
        amount_of_payout = float(msg.text)
        await utils.update_user_balance(
            user_id=msg.from_user.id,
            amount_of_payout=amount_of_payout,
            msg2edit=state_data["msg2edit"],
            wallet_name=state_data["wallet"]
        )


@dp.message(States.create_promo_amount)
async def create_promo_amount(msg: types.Message, state: FSMContext):
    if (msg.text).isdigit():
        await state.clear()
        amount = msg.text
        await msg.answer(
            text="<b>📝 Введите название промокода (Пример: spin)</b>",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="❄️", callback_data="promo_setts")
                ]
            ]),
            parse_mode='HTML'
        )
        await state.set_state(States.create_promo_name)
        await state.update_data(amount=amount)


@dp.message(States.create_promo_name)
async def create_promo_name(msg: types.Message, state: FSMContext):
    if msg.text:
        name = msg.text
        state_data = await state.get_data()
        amount = state_data["amount"]
        promos = DB.get_all(data="name", table=DB.promocodes)
        result_api = await get_promo(name)
        print(result_api)
        if (name.lower() in promos) or (isinstance(result_api, dict) and result_api.get("success") == True):
            await msg.answer(
                text="❌ Данный промокод уже существует, введите другой:"
            )
        else:
            await state.clear()
            create_promo_name_btns = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🟢 Включить", callback_data=f"promo_ubt_enable?{msg.from_user.id}_{name}_{amount}"), types.InlineKeyboardButton(text="🔴 Выключить", callback_data=f"promo_ubt_disable?{msg.from_user.id}_{name}_{amount}")]
            ])
            text = """<b>         
💬 Выберите включить ли отыгрыш промокода.

<blockquote>❗️Для УБТ (Условно бесплатный трафик) рекомендуем оставлять его отключенным, а включенным только для профессионалов схемного траффика.</blockquote></b>
"""
            await msg.answer(
                text=text,
                reply_markup=create_promo_name_btns,
                parse_mode='HTML'
            )
            
                
@dp.message(States.edit_promo_amount)
async def edit_promo_amount(msg: types.Message, state: FSMContext):
    if (msg.text).isdigit():
        new_amount = msg.text
        state_data = await state.get_data()
        promo_name = state_data["promo_name"]
        promo = await api.get_promo(promo_name)
        promo_ubt = promo["data"]["shouldWager"]
        await state.clear()
        try:
            cursor.execute(f"UPDATE promocodes SET amount = ? WHERE name = ?", (new_amount, promo_name))
            conn.commit()
            api_result = await api.edit_promo(
                {
                    'name': promo_name,
                    'amount': new_amount,
                    'shouldWager': promo_ubt,
                }
            )
            if api_result["success"] is True:
                await msg.answer(
                    text="✅️ Промокод успешно отредактирован!",
                )
            else:
                raise Exception
        except Exception:
            await msg.answer(
                text="❌ При редактировании промокода произошла ошибка!",
            )    



@dp.message(States.edit_info)
async def edit_info(msg: types.Message, state: FSMContext):
    if msg.text:
        try:
            DB.update_without_user_id(column="info", new_data=msg.html_text, table=DB.bot_info)
            await msg.answer("✅️ Информация сохранена!")
            await state.clear()
        except Exception as e:
            await msg.answer(f"❌ При сохранении информации произошла ошибка!")


@dp.message(States.edit_url)
async def edit_info(msg: types.Message, state: FSMContext):
    if msg.text:
        try:
            DB.update_without_user_id(column="actual_url", new_data=msg.text, table=DB.bot_info)
            await msg.answer("✅️ Актуальный домен сохранен!")
            await state.clear()
        except Exception as e:
            await msg.answer(f"❌ При сохранении домена произошла ошибка!")



@dp.message(States.edit_worker_perc)
async def edit_worker_perc(msg: types.Message, state: FSMContext):
    if (msg.text).isdigit():
        try:
            state_data = await state.get_data()
            worker_id = state_data["worker_id"]
            new_perc = msg.text
            result = DB.update(user_id=worker_id, column="percentage", new_data=new_perc, table=DB.users_table)
            result2 = DB.update(user_id=worker_id, column="percentage_edit_type", new_data="manual", table=DB.users_table)
            if result and result2:
                await msg.answer("✅️ Процент воркера успешно изменен!")
                await state.clear()
            else:
                raise Exception
        except Exception:
            await msg.answer("❌ При изменении процента воркера произошла ошибка!")


@dp.message(States.admin_ad)
async def admin_ad(msg: types.Message, state: FSMContext):
    if msg.text:
        btns = [
            [types.InlineKeyboardButton(text="❌ Отменить", callback_data="adminMsg_cancel"), types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="adminMsg_accept")]
        ]

        await msg.answer(
            text="❗Подтвердите текст рассылки",
        )
        await msg.answer(
            text=msg.text,
            entities=msg.entities,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns)
        )
        await state.clear()


@dp.message(States.admin_perc_change_all)
async def admin_perc_change_all(msg: types.Message, state: FSMContext):
    if (msg.text).isdigit():
        await state.clear()
        msg2edit = await msg.answer(
            text="⏳ Изменяю..."
        )
        new_perc = msg.text
        users = DB.get_all("user_id", DB.users_table)
        for user_id in users:
            DB.update(
                user_id=user_id,
                column="percentage",
                new_data=int(new_perc),
                table=DB.users_table
            )
        else:
            await msg2edit.edit_text(
                text="✅️ Процент у всех трафферов был изменен!"
            )
            

@dp.message(States.admin_perc_change_manual)
async def admin_perc_change_manual(msg: types.Message, state: FSMContext):
    if (msg.text).isdigit():
        await state.clear()
        msg2edit = await msg.answer(
            text="⏳ Изменяю..."
        )
        new_perc = msg.text
        users = DB.get_all("user_id", DB.users_table)
        for user_id in users:
            if DB.get(user_id=user_id, data="percentage_edit_type", table=DB.users_table) == "auto":
                DB.update(
                    user_id=user_id,
                    column="percentage",
                    new_data=int(new_perc),
                    table=DB.users_table
                )
            else:
                continue
        else:
            await msg2edit.edit_text(
                text="✅️ Процент у всех трафферов, кроме тех, кому меняли вручную был изменен!"
            )
            

@dp.message(States.user_input)
async def user_input(msg: types.Message, state: FSMContext):
    if msg.text:
        await state.clear()
        if msg.text.startswith("@"):
            worker_username = msg.text.split("@")[1]
            cursor.execute(f"SELECT user_id FROM {DB.users_table} WHERE tg_username = ?", (worker_username, ))
            worker_id = cursor.fetchone()[0]
            if worker_id is not None:
                text, worker_btns = await utils.create_worker_profile(worker_id)
                await msg.answer(
                    text=text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=worker_btns)
                )
        else:
            worker_id = msg.text
            result = DB.get(user_id=worker_id, data="user_id", table=DB.users_table)
            if result is not None:
                text, worker_btns = await utils.create_worker_profile(worker_id)
                await msg.answer(
                    text=text,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=worker_btns)
                )

@dp.message(States.user_input_new_balance)
async def user_input_new_balance(msg: types.Message, state: FSMContext):
    if msg.text:
        # if msg.text.isdigit():
        data = await state.get_data()
        worker_id = data.get("worker_id")
        await state.clear()
        DB.update(user_id=worker_id, column="balance", new_data=float(msg.text), table=DB.users_table)

        await msg.answer("✅️ Баланс воркера был успешно изменен")


@dp.message()
async def messages_handler(msg: types.Message):
    if msg.text == "☃️ Профиль":
        await msg.delete()
        await utils.show_user_profile(msg=msg)
        
    elif msg.text == "⚙️ Настройки":
        materials_btns = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎟 Промокоды", callback_data="promo_setts")],
            [types.InlineKeyboardButton(text="❄️", callback_data="back_main")]
        ])
        await msg.delete()
        await msg.answer(
            text="⚙️ Настройки",
            reply_markup=materials_btns
        )

    elif msg.text == "🌏 Актуальные домены":
        actual_url = DB.get_without_user_id(data="actual_url", table=DB.bot_info)
        text = f'''
🌏 Актуальные домены:
<blockquote>➖ {actual_url}</blockquote>'''

        await msg.delete()
        await msg.answer(
            text=text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❄️", callback_data="back_main")]]),
            parse_mode='HTML'
            
        )
    elif msg.text == "📄 Информация":
        text = DB.get_without_user_id(data="info", table=DB.bot_info)
        text = f'''
📄 Информация'''
        await msg.delete()
        await msg.answer(
            text=text,
            reply_markup = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="⛄️ Вступить во все чаты", url="https://t.me/addlist/WJwrxYGqRpMzODE0")],
                    [types.InlineKeyboardButton(text="❄️", callback_data="back_main")]
                ]
            ),
            parse_mode="HTML"
        )

