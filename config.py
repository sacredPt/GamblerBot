import configparser
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from log import create_logger
import aiogram
from aiogram.filters import CommandStart, Command
from typing import List
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
import asyncio
from aiogram import types
from aiogram import F
from state import States
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter

read_config = configparser.ConfigParser()
dp = Dispatcher(storage=MemoryStorage())
logger = create_logger(__name__)

db_DIR = "database/"

read_config.read("config.ini") 

config = read_config['config'] # Словарь с данными из config.ini
bot_token = config["bot_token"] if config["bot_token"] is not None else logger.error("Empty parameter for bot_token")
ADMIN_IDS = str(config["admin_id"]).split(",") if config["admin_id"] is not None else logger.error("Empty parameter for admin_id")
API_TOKEN = config["api_token"] if config["api_token"] is not None else logger.error("Empty parameter for api_token")
GROUP_ID = config["group_id"] if config["group_id"] is not None else logger.error("Empty parameter for group_id")
CHANNEL_ID = config["channel_id"] if config["channel_id"] is not None else logger.error("Empty parameter for channel_id")
USERS_PAYOUTS = config["users_payouts"] if config["users_payouts"] is not None else logger.error("Empty parameter for users_payouts")




# Проверка на правильность токена бота
try:
    bot = Bot(token=bot_token)
except aiogram.utils.token.TokenValidationError:
    logger.critical("Bot token are empty or invalid")