import time
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import json
import socket
import threading
from data_process import string_to_binary_string, binary_string_to_string

app = Flask(__name__)
socketio = SocketIO(app)

class Client:
    def __init__(self, config_file='../config.json', flag=0):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.server_host = config.get('host', 'localhost')
        if flag == 0:
            self.server_port = int(config.get('port', 12345))
        else:
            self.server_port = int(config.get('test_port', 12346))
        self.client = None

    def input_command(self, command):
        opt = command.split(' ')
        # 使用 getattr 从对象 obj 中获取方法
        method = getattr(self, opt, None)
        args = command[1:]
        if callable(method):
            return method(*args)
        else:
            return f"Method '{opt}' not found"

    def query_flight(self, source_place: str, destination: str):
        query_str = "query_flight" + ";" + source_place + ";" + destination
        return self.send_request(query_str)

    def query_flight_info(self, flight_id: int):
        query_str = "query_flight_info" + ";" + str(flight_id)
        return self.send_request(query_str)

    def reserve_seats(self, flight_id: int, seats_count: int, reserve_result=None):
        transfer_str = "reserve_seats" + ";" + str(flight_id) + ";" + str(seats_count)
        return self.send_request(transfer_str, reserve_result)

    def monitor_update(self, flight_id: int, period_time: int, monitor_result=None):
        transfer_str = "monitor_update" + ";" + str(flight_id) + ";" + str(period_time)
        return self.send_request(transfer_str, monitor_result)

    # todo marshall and unmarshall
    def send_request(self, data: str, monitor_result=None):
        # string to 01
        binary_data = string_to_binary_string(data)
        response_received = threading.Event()
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client.sendto(binary_data.encode('utf-8'), (self.server_host, self.server_port))
            self.local_ip, self.local_port = self.client.getsockname()
            if data.startswith("monitor_update"):
                # 创建一个线程来处理接收消息
                def receive_messages():
                    while True:
                        response, _ = self.client.recvfrom(2048)
                        # 01 to string
                        response_text = binary_string_to_string(response.decode('utf-8'))
                        print(f"Client {self.local_ip}:{self.local_port}: 从服务器接收到的响应: {response_text}")
                        socketio.emit('monitor_update', {'data': response_text})
                        if monitor_result is not None:
                            monitor_result['received_updates'].append(response_text)
                        if response_text.startswith("monitor finished"):
                            response_received.set()
                            break
                # 启动接收消息的线程
                receiver_thread = threading.Thread(target=receive_messages)
                receiver_thread.start()
                return response_received.wait()
            else:
                response, _ = self.client.recvfrom(2048)
                response_text = binary_string_to_string(response.decode('utf-8'))
                print(f"Client {self.local_ip}:{self.local_port}: 从服务器接收到的响应: {response_text}")
                if monitor_result is not None:
                    monitor_result['received_updates'].append(response_text)
                return 0, response_text
        except socket.timeout:
            return 1, f"Client {self.local_ip}:{self.local_port}: Request timed out"
        except Exception as e:
            return 1, f"Client {self.local_ip}:{self.local_port}: " + str(e)
        finally:
            if self.client:
                # 关闭 socket
                self.client.close()

client = Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query_flight', methods=['POST'])
def query_flight():
    data = request.get_json()
    source_place = data['source_place']
    destination = data['destination']
    code, response = client.query_flight(source_place, destination)
    return jsonify({'code': code, 'response': response})

@app.route('/reserve_seats', methods=['POST'])
def reserve_seats():
    data = request.get_json()
    flight_id = data['flight_id']
    seats_count = data['seats_count']
    code, response = client.reserve_seats(flight_id, seats_count)
    return jsonify({'code': code, 'response': response})

@app.route('/start_monitor', methods=['GET'])
def start_monitor():
    flight_id = request.args.get('flightId')
    period_time = int(request.args.get('periodTime'))
    client.monitor_update(int(flight_id), period_time)
    return "Monitoring started"

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

    # socketio.run(app, host='10.91.220.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

# if __name__ == "__main__":
#     test_client = templates()
#     # test_client.query_flight("Beijin", "Los Angeles")
#     # test_client.monitor_update(101, 1)
#     test_client.query_flight_info(101)
#     time.sleep(2)
#     test_client.monitor_update(101, 2)

