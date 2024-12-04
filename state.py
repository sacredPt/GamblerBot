from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    
    """
    Класс для FSM
    """
    start_input = State()
    start_sec_input = State()
    change_username = State()
    link_wallet = State()
    payout_amount = State()
    create_promo_amount = State()
    create_promo_name = State()
    edit_promo_amount = State()
    edit_url = State()
    edit_info = State()
    edit_worker_perc = State()
    admin_ad = State()
    admin_perc_change_all = State()
    admin_perc_change_manual = State()
    user_input = State()
    user_input_new_balance = State()