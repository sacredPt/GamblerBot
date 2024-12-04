from config import *
from db import DB
from log import create_logger
logger = create_logger(__name__)


@dp.message(CommandStart())
async def start(msg: types.Message, state: FSMContext, user_id: int = None, edit_msg: bool = False):
    if not user_id:
        user_id = msg.from_user.id
    await state.clear()
    user_state = DB.get(user_id=user_id, data="state", table=DB.unconfirmed_users_table)
    _is_banned = DB.get(user_id=user_id, data="_is_banned", table=DB.users_table) # Проверка состояния пользователя не в основной БД
    if user_state == None:
        text='''
☃️ Добро пожаловать в команду <b>Elysium!</b>
💭 Для того чтобы подать заявку в нашу команду - вам нужно ответить на несколько вопросов!
✨ Если вы готовы - нажмите на кнопку под этим сообщением.

'''
        btns = [
            [types.InlineKeyboardButton(text="💭 Подать заявку", callback_data=f"send_req_zz")]
        ]
        
        await msg.answer(
            text, 
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns),
            parse_mode='HTML'
        )
        #await state.set_state(States.start_input)
    
    elif user_state == "wait":
        await msg.answer("🧐 Ваша заявка уже находится на рассмотрении, ожидайте")
        
    elif user_state == "confirmed":
        if _is_banned == "False":
            _is_user_in_main_db = DB.get(user_id=user_id, data="user_id", table=DB.users_table) # Проверка есть ли пользователь в основной БД
            if _is_user_in_main_db is not None:
                start_btns = types.ReplyKeyboardMarkup(keyboard=[
                    [types.KeyboardButton(text="☃️ Профиль"), types.KeyboardButton(text="🌏 Актуальные домены")],
                    [types.KeyboardButton(text="⚙️ Настройки"), types.KeyboardButton(text="📄 Информация")]
                ], resize_keyboard=True)
                if edit_msg is True:
                    await msg.delete()
                    await msg.answer(
                        text="⚙️ Главное меню!",
                        reply_markup=start_btns
                    )
                    
                    
                else:
                    await msg.answer(
                        text="⚙️ Главное меню",
                        reply_markup=start_btns
                    )
        else:
            await msg.answer("Вы были заблокированы!")
    elif user_state == "unconfirmed":
        await msg.answer(f"❌ Заявка была отклонена, для уточнения причины свяжитесь с администрацией - {config['admin_username']}")



@dp.message(Command("admin"))
async def admin(msg: types.Message, state: FSMContext, user_id: int = None, edit_msg: bool = False):
    await state.clear()
    if not user_id: user_id = msg.from_user.id
    if str(user_id) in ADMIN_IDS:
        admin_btns = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="👥 Воркеры", callback_data="admin_workers"), types.InlineKeyboardButton(text="🥇 Топ воркеров", callback_data="admin_topWorkers")],
            [types.InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"), types.InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_msg")],
            [types.InlineKeyboardButton(text="💰 Депозиты", callback_data="admin_deposits"), types.InlineKeyboardButton(text="🌏 Актуальные домены", callback_data="admin_url")],
            [types.InlineKeyboardButton(text="📄 Информация", callback_data="admin_info"), types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")],
        ])
        text = '⚙️ Панель администратора'
        if edit_msg is True:
            await msg.edit_text(
                text=text, 
                reply_markup=admin_btns
            )
        else:
            await msg.answer(
                text=text, 
                reply_markup=admin_btns
            )
    else:
        pass



@dp.message(Command("user"))
async def user(msg: types.Message, state: FSMContext):
    if str(msg.from_user.id) in ADMIN_IDS:
        await state.clear()
        await msg.answer("Отправь его id или тег")
        await state.set_state(States.user_input)