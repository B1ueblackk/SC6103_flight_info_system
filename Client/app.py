import sys
import time
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import SocketIO
import json
import socket
import threading
from data_process import string_to_binary_string, binary_string_to_string
from server import Server

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # 用于 session 加密
socketio = SocketIO(app)

try:
    with open("../config.json", 'r') as f:
        config = json.load(f)
        f.close()
except FileNotFoundError:
    with open("config.json", 'r') as f:
        config = json.load(f)
        f.close()

class Client:
    def __init__(self, config_file='../config.json', flag=0):
        # with open(config_file, 'r') as f:
        #     config = json.load(f)
        self.server_host = config.get('host', 'localhost')
        if flag == 0:
            self.server_port = int(config.get('port', 12345))
        else:
            self.server_port = int(config.get('test_port', 12346))
        f.close()

    def input_command(self, command):
        opt = command.split(' ')
        method = getattr(self, opt, None)
        args = command[1:]
        if callable(method):
            try:
                return method(*args)
            except Exception as e:
                return 1, f"error: {str(e)}"
        else:
            return 1, f"Method '{opt}' not found"

    def login(self, username, password):
        query_str = "login" + ";" + username + ";" + password
        return self.send_request(query_str)

    def register(self, username, password):
        query_str = "register" + ";" + username + ";" + password
        return self.send_request(query_str)

    def logout(self):
        query_str = "logout"
        return self.send_request(query_str)

    def query_flight(self, source_place: str, destination: str):
        query_str = "query_flight" + ";" + source_place + ";" + destination
        return self.send_request(query_str)

    def query_flight_info(self, flight_id: int):
        query_str = "query_flight_info" + ";" + str(flight_id)
        return self.send_request(query_str)

    def reserve_seats(self, flight_id: int, seats_count: int, order_id: str, reserve_result=None):
        transfer_str = "reserve_seats" + ";" + str(flight_id) + ";" + str(seats_count) + ";" + str(order_id)
        return self.send_request(transfer_str, reserve_result)

    def monitor_update(self, flight_id: int, period_time: int, monitor_result=None):
        transfer_str = "monitor_update" + ";" + str(flight_id) + ";" + str(period_time)
        return self.send_request(transfer_str, monitor_result)

    def query_all_orders(self):
        transfer_str = "query_all_orders"
        return self.send_request(transfer_str)

    def query_order(self, order_id):
        transfer_str = "query_order" + ";" + str(order_id)
        return self.send_request(transfer_str)

    def send_request(self, data: str, monitor_result=None):
        if session.get('username') is None:
            if data.split(';')[0] != "register" and data.split(';')[0] != "login":
                return 1, "Need login first!"
        else:
            data += ";" + session['username']

        binary_data = string_to_binary_string(data)
        response_received = threading.Event()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                client_socket.sendto(binary_data.encode('utf-8'), (self.server_host, self.server_port))
                local_ip, local_port = client_socket.getsockname()
                if data.startswith("monitor_update"):
                    def receive_messages():
                        complete_response = ""
                        while True:
                            response, _ = client_socket.recvfrom(2048)
                            complete_response += response.decode('utf-8')
                            if "END" in complete_response:
                                complete_response = complete_response.replace("END", "")
                            try:
                                response_obj = json.loads(binary_string_to_string(complete_response))
                                print(f"Client {local_ip}:{local_port}: 从服务器接收到的完整响应: {response_obj}")
                                socketio.emit('monitor_update', {'data': response_obj['message']})
                                complete_response = ""
                                if monitor_result is not None:
                                    monitor_result['received_updates'].append(response_obj['message'])
                                if response_obj['message'].startswith("monitor finished"):
                                    response_received.set()
                                    break
                            except json.JSONDecodeError:
                                continue

                    receiver_thread = threading.Thread(target=receive_messages)
                    receiver_thread.start()
                    return response_received.wait()
                else:
                    complete_response = ""
                    while True:
                        response, _ = client_socket.recvfrom(2048)
                        complete_response += response.decode('utf-8')
                        if "END" in complete_response:
                            complete_response = complete_response.replace("END", "")
                        try:
                            response_obj = json.loads(binary_string_to_string(complete_response))
                            return response_obj['flag'], response_obj['message']
                        except json.JSONDecodeError:
                            continue
        except socket.timeout:
            return 1, f"Client {local_ip}:{local_port}: Request timed out"
        except Exception as e:
            return 1, f"Client {local_ip}:{local_port}: " + str(e)

client = Client()

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login_html'))

@app.route('/index.html')
def index():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/login.html')
def login_html():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if 'user_address' not in session:
        return jsonify({'code': 2, 'response': "please login metamask!"})
    data = request.get_json()
    username = data['username']
    password = data['password']
    code, response = client.login(username, password)
    if code == 0:
        session['username'] = username
    return jsonify({'code': code, 'response': response})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    code, response = client.register(username, password)
    # 注册逻辑
    return jsonify({'code': code, 'response': response})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'code': 0, 'message': 'Logout successful'})

@app.route('/query_flight', methods=['POST'])
def query_flight():
    if 'username' not in session:
        return jsonify({'code': 1, 'response': 'User not logged in'})
    data = request.get_json()
    source_place = data['source_place']
    destination = data['destination']
    code, response = client.query_flight(source_place, destination)
    return jsonify({'code': code, 'response': response})

@app.route('/query_flight_info', methods=['POST'])
def query_flight_info():
    if 'username' not in session:
        return jsonify({'code': 1, 'response': 'User not logged in'})
    data = request.get_json()
    flight_identifier = data['source_place']
    code, response = client.query_flight_info(flight_identifier)
    return jsonify({'code': code, 'response': response})

@app.route('/reserve_seats', methods=['POST'])
def reserve_seats():
    if 'username' not in session:
        return jsonify({'code': 1, 'response': 'User not logged in'})
    data = request.get_json()
    flight_id = data['flight_id']
    seats_count = data['seats_count']
    order_id = data['order_id']
    code, response = client.reserve_seats(flight_id, seats_count, order_id)
    return jsonify({'code': code, 'response': response})

@app.route('/save_address', methods=['POST'])
def save_address():
    try:
        data = request.get_json()
        user_address = data['walletAddress']
        session['user_address'] = user_address
        return jsonify({'code': 0, 'message': "Login metamask success!"})
    except Exception as e:
        print(f"save address error:{str(e)}")
        return jsonify({'code': 1, 'message': 'Error when login metamask!'})


@app.route('/check_login', methods=['GET'])
def check_login():
    print(session)
    if 'username' in session:
        return jsonify({'code': 0, 'message': 'Logged in'})
    else:
        return jsonify({'code': 1, 'message': 'Not logged in'})

@app.route('/start_monitor', methods=['GET'])
def start_monitor():
    flight_id = request.args.get('flightId')
    period_time = request.args.get('periodTime')
    if flight_id == '' or period_time == '':
        return json.dumps({"code": 1, "response": "Bad Params!"})
    client.monitor_update(int(flight_id), int(period_time))
    return json.dumps({"code": 0, "response": "Monitor Started!"})

@app.route('/query_order', methods=['POST'])
def query_order():
    try:
        data = request.get_json()
        order_id = data['order_id']
        if order_id is  None or not order_id.isdigit():
            return json.dumps({"code": 1, "response": "Bad Params!"})
        code, response = client.query_order(order_id)
        return json.dumps({"code": code, "response": response})
    except Exception as e:
        print(f"query order error:{str(e)}")
        return json.dumps({"code": 1, "response": "Query Failed!"})

@app.route('/query_all_orders', methods=['POST'])
def query_all_orders():
    try:
        code, response = client.query_all_orders()
        return json.dumps({"code": code, "response": response})
    except Exception as e:
        print(f"query orders error:{str(e)}")
        return json.dumps({"code": 1, "response": "Query Failed!"})

if __name__ == "__main__":
    print("Client start.", file=sys.stderr)
    # socketio.run(app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True)
    socketio.run(app, allow_unsafe_werkzeug=True)