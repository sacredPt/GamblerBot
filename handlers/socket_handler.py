import socketio
import sys, os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
import utils


sio = socketio.Client()

@sio.event
def connect():
    print("Connected successfully")

@sio.event
def connect_error(data):
    print("Failed to connect:", data)

@sio.event
def disconnect():
    print("Disconnected from server")
    

@sio.event
def newDeposit(data):
    print("New deposit!")
    utils.send_newDeposit(data)
    sio.emit('DepositReceived', data)

def main():
    max_retries = 20000 # максимальное количество попыток
    delay = 5        # задержка в секундах между попытками

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt} to connect...")
            sio.connect(
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
            time.sleep(delay)

def run():
    main()
    sio.wait()

if __name__ == "__main__":
    main()
    sio.wait()
