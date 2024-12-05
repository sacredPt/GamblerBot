import asyncio
from pprint import pprint
import socketio
import sys, os
import time
import logging
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
import utils


sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected successfully")

@sio.event
async def connect_error(data):
    print("Failed to connect:", data)

@sio.event
async def disconnect():
    print("Disconnected from server")

@sio.event
async def newDeposit(data):
    print(data)
    print("New deposit!")
    await utils.send_newDeposit(data)
    await sio.emit('DepositReceived', data)
    
@sio.event
async def newMessage(data):
    #print(data)
    
    await utils.send_newMessage(data)
    
    print("New Message!")

async def main():
    max_retries = 20000
    delay = 5

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt} to connect...")
            await sio.connect(
                'https://gambler-panel.com',
                headers={
                    'Authorization': f'Worker {config.API_TOKEN}',
                    'x-connection-type': 'bot'
                },
                socketio_path='/api/socket.io'
            )
            break
        except Exception as e:
            print(f"Connection attempt {attempt} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(delay)
            else:
                print("Max retries reached. Could not connect.")
                break


async def run():
    await main()
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(run())

