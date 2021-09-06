from flask import Flask, send_from_directory, render_template, Response, request
from flask_socketio import SocketIO, emit
import json
import asyncio
from redis import Redis
from threading import Thread
from datetime import datetime

messages = []
message_limit_sec = {}
bans = {}

app = Flask('python_simple_chat_server')
socketio = SocketIO(app)
redis = Redis()
redis_name = 'websocket_messaging_messages'

@app.route('/<path:path>')
def url_from_path(path: str):
    return send_from_directory('static/', path)

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html', messages=get_all_messages())

@app.route('/get')
def chat_get():
    resp = Response(headers={'content-type':'application/json'})
    if (len(messages) > 0):
        resp.set_data(json.dumps(get_all_messages()))
        return resp
    entry = redis.get(redis_name)
    if entry is None:
        resp.set_data('[]')
        return 
    resp.set_data(entry)
    return resp

@socketio.on('message')
def ws_receiver(data):
    # print(str(type(data)) + ': ' + str(data))
    if request.remote_addr in bans:
        if bans[request.remote_addr] < datetime.now().timestamp():
            bans.pop(request.remote_addr)
        else:
            return emit('error', f'You have been banned because of flooding, will last on {datetime.fromtimestamp(bans[request.remote_addr]).isoformat()}')
    if not ('from' in data and 'value' in data and type(data['from']) is str and type(data['value']) is str): return emit('error', 'Your payload is not valid')
    from_user: str = data['from'].replace(' ', '')
    message_text: str = data['value'].replace("\n", '').replace("\r", '').strip()
    if len(from_user) == 0 or len(message_text.replace(' ', '')) == 0: return emit('error', 'Your name or message is empty')
    points = 5
    points += len(from_user) / 3.75
    if len(from_user) > 30:
        from_user = from_user[:30]
    points += len(message_text) / 512
    if len(message_text) > 4096:
        message_text = message_text[:4096]
    if request.remote_addr in message_limit_sec:
        message_limit_sec[request.remote_addr] += points
        if message_limit_sec[request.remote_addr] > 100:
            bans[request.remote_addr] = datetime.now().timestamp() + 43200
    else:
        message_limit_sec[request.remote_addr] = points
    message = {'from': from_user, 'value': message_text}
    messages.append(message)
    socketio.emit('receive', message)

def save_thread():
    asyncio.run(save_loop())

async def save_loop():
    while True:
        await save_timer(2)

async def save_timer(seconds: int):
    await save_everything()
    await asyncio.sleep(seconds)

async def save_everything():
    global messages
    global message_limit_sec
    if len(messages) == 0: return
    print('saving everything in database')
    redis.set(redis_name, json.dumps(get_all_messages()))
    messages.clear()
    message_limit_sec.clear()

def get_all_messages():
    db_entry = redis.get(redis_name)
    dump_entry = []
    if db_entry != None:
        dump_entry.extend(json.loads(db_entry))
    if len(messages) > 0:
        dump_entry.extend(messages)
    return dump_entry

if __name__ == "__main__":
    print('spawning save_thread')
    thread = Thread(target=save_thread)
    thread.daemon = True
    thread.start()
    print('entering loop')
    socketio.run(app, port=5690, host='0.0.0.0')
