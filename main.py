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
    '''
    Запуск бота и socket_handler.py в разных процессах
    
    socket_process = await asyncio.create_subprocess_exec(
        sys.executable, '-u', 'handlers/socket_handler.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    pid = socket_process.pid
    logger.info(f"Started socket_handler with PID {pid}")
    '''
    Thread(target=run).start()
    tasks = [
        asyncio.create_task(start_bot()),
   #     utils.read_subprocess_output(socket_process.stdout),
    #    utils.read_subprocess_output(socket_process.stderr),
    ]
    await asyncio.gather(*tasks)
if __name__ == '__main__':
    DB.run()
    asyncio.run(tasks(), debug=False)
