import sys
from threading import Thread
from config import *
from db import DB
import handlers.inline_handler
import handlers.msg_handler
import handlers.cmd_handler
from log import create_logger
import utils
from handlers.socket_handler import run
logger = create_logger(__name__)
async def start_bot():
    await dp.start_polling(bot, close_bot_session=False, handle_signals=False)



async def tasks():
    asyncio.create_task(run())
    
    tasks = [asyncio.create_task(start_bot())]
    
    await asyncio.gather(*tasks)
       
if __name__ == '__main__':
    DB.run()
    asyncio.run(tasks(), debug=False)
