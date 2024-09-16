from flask import Flask
import json
import os
import socket
import threading
import time
from datetime import datetime, timedelta
import bcrypt
from data_process import binary_string_to_string, string_to_binary_string
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

try:
    with open("../config.json", 'r') as f:
        config = json.load(f)
        f.close()
except FileNotFoundError:
    with open("config.json", 'r') as f:
        config = json.load(f)
        f.close()

class Server:
    def __init__(self, config_file='../config.json',flag=0):
        print("Server: Server starting...")
        self.host = config.get('host', 'localhost')
        if flag == 0:
            self.port = int(config.get('port', 12345))
        else:
            self.port = int(config.get('test_port', 12346))
        print(f"Server: Server ip: {self.host}:{self.port}")
        self.server_socket = None
        self.client_address = None
        self.monitor_dict = {}
        self.user_dict = {}
        self.running = False
        try:
            self.connect_database(flag=flag)
        except Exception as e:
            print("Server: connect failed\n", str(e))

    def connect_database(self, flag: int = 0):
        db_username = os.getenv("db_username")
        db_pwd = os.getenv("db_pwd")
        uri = f"mongodb+srv://{db_username}:{db_pwd}@cluster0.osgx6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

        if flag == 0:
            database_name = config['mongodb']['database']
        else:
            database_name = config['mongodb']['test_database']

        client = MongoClient(uri, server_api=ServerApi('1'))
        # 选择数据库
        db = client[database_name]
        # 选择集合
        self.flight_info_collection = db[database_name]
        self.user_collection = db["user_info"]
        self.order_collection = db["order_info"]

    def start_listening(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(1)  # 设置超时时间为1秒
        print(f"Server: UDP 服务器已启动，正在监听 {self.host}:{self.port}...")
        try:
            while self.running:
                try:
                    data, self.client_address = self.server_socket.recvfrom(1024)
                    text = binary_string_to_string(data.decode('utf-8'))
                    print(f"Server: 接收到来自 {self.client_address} 的数据: {text}")
                    ret_flag, ret_msg = self.handle_request(text)
                    # 构造要发送的响应
                    response = json.dumps({'flag': ret_flag, 'message': ret_msg, "receiver": self.client_address})
                    self.chunk_data(response, self.client_address)
                except socket.timeout:
                    # 超时检查，避免无限等待
                    continue
        except Exception as e:
            print("Server: start listening failed: " + str(e))
        finally:
            self.server_socket.close()
            print("Server: 服务器已关闭")

    def chunk_data(self, str_to_send: str, address):
        response_binary = string_to_binary_string(str_to_send).encode('utf-8')
        # 分段发送，每次1024字节
        CHUNK_SIZE = 1024
        for i in range(0, len(response_binary), CHUNK_SIZE):
            chunk = response_binary[i:i + CHUNK_SIZE]
            is_last_chunk = (i + CHUNK_SIZE >= len(response_binary))  # 是否是最后一个chunk
            self.server_socket.sendto(chunk + (b'END' if is_last_chunk else b''), address)
        print(f"Server: 数据{str_to_send} 已发送给 {address}")

    def stop_listening(self):
        if not self.running:
            return
        self.running = False
        # 在关闭之前检查是否已经初始化
        if self.server_socket:
            self.server_socket.close()
        print("Server: 服务器已停止监听")

    def handle_request(self, data: str) -> (int, str):
        try:
            opt = data.split(';')[0]
            username = data.split(';')[-1]
            if opt != "register" and not self.user_collection.find_one({'username': username}):
                return 1, "Wrong username!"

            method = getattr(self, opt, None)
            if callable(method):
                return method(data)
            else:
                return f"Method '{opt}' not found"
        except Exception as e:
            return 1, str(e)

    def add_flight(self, flight_identifier, source_place, destination_place, departure_time, airfare, seat_availability):
        flight_document = {
             "flight_identifier": flight_identifier,
             "source_place": source_place,
             "destination_place": destination_place,
             "departure_time": departure_time,
             "airfare": airfare,
             "seat_availability": seat_availability
        }

        # 插入文档到集合中
        self.flight_info_collection.insert_one(flight_document)
        # self.flight_info_collection.create_index([("flight_identifier", 1)], unique=True)

    def init(self, data: str) -> (int, str):
        username = data.split(';')[1]
        if not self.user_is_valid(username):
            return 1, "Wrong username!"
        return 0, self.get_top_flights()

    def register(self, data: str) -> (int, str):
        username = data.split(';')[1]
        password = data.split(';')[2]
        if self.user_collection.find_one({"username": username}):
            return 1, "User already exists!"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.user_collection.insert_one({"username": username, "password": hashed_password})
        return 0, "User registered successfully!"

    def login(self, data: str) -> (int, str):
        username = data.split(';')[1]
        password = data.split(';')[2]
        user = self.user_collection.find_one({"username": username})
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return 1, "Invalid credentials!"
        return 0, "Login successfully!"

    # 返回标志位(0:success, 1:fail) + 所有符合条件的航班信息/错误信息
    def query_flight(self, data: str) -> (int, str):
        try:
            source_place = data.split(';')[1]
            destination_place = data.split(';')[2]
            username = data.split(';')[3]
            query = {
                "source_place": source_place,
                "destination_place": destination_place
            }
            projection = {
                "_id": 0,
            }
            # 执行查询并应用投影
            cursor = self.flight_info_collection.find(query, projection)
            # 将所有匹配的航班信息添加到返回列表中
            from datetime import datetime

            ret = [{
                'flight_identifier': flight['flight_identifier'],
                'source_place': flight['source_place'],
                'destination_place': flight['destination_place'],
                'departure_time': datetime.strptime(flight['departure_time'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime(
                    '%Y-%m-%dT%H:%M:%S') if isinstance(flight['departure_time'], str) else flight[
                    'departure_time'].strftime('%Y-%m-%dT%H:%M:%S'),
                'airfare': flight['airfare'],
                'seat_availability': flight['seat_availability']
            } for flight in cursor]
            if len(ret) == 0:
                return 1, f"No flights matched {source_place} to {destination_place}!"
            return 0, json.dumps(ret)
        except Exception as e:
            return 1, f"query flight failed: {str(e)}"

    # 返回标志位(0:success, 1:fail) + 对应航班信息/错误信息
    def query_flight_info(self, data: str) -> (int, str):
        try:
            flight_identifier = int(data.split(';')[1])
            flight_info = self.flight_info_collection.find_one(
                {
                    "flight_identifier": flight_identifier
                },
                projection = {
                    "_id": 0
                }
            )
            if flight_info:
                ret = {
                    'flight_identifier': flight_info['flight_identifier'],
                    'source_place': flight_info['source_place'],
                    'destination_place': flight_info['destination_place'],
                    'departure_time': flight_info['departure_time'].strftime('%Y-%m-%dT%H:%M:%S'),
                    'airfare': flight_info['airfare'],
                    'seat_availability': flight_info['seat_availability']
                }

                return 0, json.dumps(ret)
            return 1, f"No flights matched {flight_identifier}!"
        except Exception as e:
            return 1, f"query flight info failed: {str(e)}"

    def reserve_seats(self, data: str) -> (int, str):
        try:
            # 解析传入的数据
            flight_identifier = int(data.split(';')[1])
            seats_count = int(data.split(';')[2])
            order_id = data.split(';')[3]
            username = data.split(';')[4]

            # 查找航班信息
            flight_info = self.flight_info_collection.find_one({"flight_identifier": flight_identifier})
            if flight_info is None:
                return 1, f"No such flight {flight_identifier}!"
            # 检查座位数量是否足够
            if flight_info["seat_availability"] < seats_count:
                return 1, "Seats not enough!"
            user_info = self.user_collection.find_one({"username": username})
            # 检查用户是否存在
            if user_info is None:
                return 1, "User does not exist!"

            # 更新座位数量
            new_seat_availability = flight_info["seat_availability"] - seats_count
            self.flight_info_collection.update_one(
                {"flight_identifier": flight_identifier},
                {"$set": {"seat_availability": new_seat_availability}}
            )
            self.order_collection.insert_one(
                {
                    "id": order_id,
                    "flight_identifier": flight_identifier,
                    "reserver": username,
                    "seats": seats_count
                }
            )
            self.reserve_seats_callback(flight_identifier, new_seat_availability)
            return 0, json.dumps({'id': order_id})
        except Exception as e:
            return 1, f"reserve seats failed: {str(e)}"

    def reserve_seats_callback(self, flight_identifier, new_seat_availability):
        if flight_identifier in self.monitor_dict:
            monitor_list = self.monitor_dict[flight_identifier]
            for monitor in monitor_list:
                if datetime.now() < monitor["end_time"]:
                    response = f"flight-{flight_identifier} seats' availability updates: {new_seat_availability} at {datetime.now()}"
                    ret = json.dumps({"code": 0, "message": response, "receiver": monitor["client_address"]})
                    self.chunk_data(ret, monitor["client_address"])


    def cleanup_expired_monitors(self):
        current_time = datetime.now()
        for flight_identifier in list(self.monitor_dict.keys()):
            # 过滤掉结束时间小于当前时间的监听记录
            self.monitor_dict[flight_identifier] = [
                monitor for monitor in self.monitor_dict[flight_identifier]
                if monitor["end_time"] > current_time
            ]
            # 如果航班号的监听列表为空，删除这个航班号的记录
            if not self.monitor_dict[flight_identifier]:
                del self.monitor_dict[flight_identifier]

    def monitor_update(self, data: str) -> (int, str):
        try:
            # 解析输入数据
            flight_identifier = int(data.split(';')[1])
            monitor_period = int(data.split(';')[2])
            # 计算监听的结束时间
            current_time = datetime.now()
            end_time = current_time + timedelta(minutes=monitor_period)

            # 更新监听字典
            if flight_identifier not in self.monitor_dict:
                self.monitor_dict[flight_identifier] = []
            if self.client_address not in self.user_dict:
                self.user_dict[self.client_address] = (flight_identifier, end_time)
            else:
                return 1, "One client can only monitor on flight!"

            for monitor in self.monitor_dict[flight_identifier]:
                if self.client_address == monitor["client_address"] and monitor["end_time"] > end_time:
                    return 1, "Monitoring already exists!"

            monitor_info = {
                "client_address": self.client_address,
                "end_time": end_time
            }

            # 添加用户监听请求，包括监听的结束时间
            self.monitor_dict[flight_identifier].append(monitor_info)

            # 启动定时线程
            monitor_thread = threading.Thread(
                target=self.monitor_end_thread,
                args=(flight_identifier, monitor_info)
            )
            monitor_thread.start()
            return 0, "Monitoring started!"
        except Exception as e:
            return 1, f"monitor update failed: {str(e)}"

    def monitor_end_thread(self, flight_identifier: int, monitor_info: dict):
        # 等待监视期结束
        end_time = monitor_info["end_time"]
        time_to_wait = (end_time - datetime.now()).total_seconds()
        if time_to_wait > 0:
            threading.Event().wait(time_to_wait)

        # 发送监视结束消息
        client_address = monitor_info["client_address"]
        message = f"Monitor finished!"
        ret = json.dumps({"code": 0, "message": message, "receiver": client_address})
        self.chunk_data(ret, client_address)
        # 从监视列表中移除
        self.monitor_dict[flight_identifier].remove(monitor_info)
        if not self.monitor_dict[flight_identifier]:
            del self.monitor_dict[flight_identifier]
        if not self.user_dict[client_address]:
            del self.user_dict[client_address]

    def query_order(self, data: str) -> (int, str):
        order_id = data.split(';')[1]
        username = data.split(';')[2]
        if not self.user_is_valid(username):
            return 1, "Invalid username!"
        order = self.order_collection.find_one({"id": order_id})
        if order is None:
            return 1, "Order not found!"
        return 0, json.dumps({"id": order_id, "reserver": order["reserver"], "flight_identifier": order["flight_identifier"], "seats": order["seats"]})

    def query_all_orders(self, data: str):
        username = data.split(';')[1]
        if not self.user_is_valid(username):
            return 1, "Invalid username!"
        cursor = self.order_collection.find({"reserver": username})
        ret = [{
            'order_id': order['id'],
            'flight_identifier': order['flight_identifier'],
        } for order in cursor]
        if len(ret) == 0:
            return 1, "No orders found!"
        return 0, json.dumps({"orders": ret})

    def user_is_valid(self, username: str):
        user = self.user_collection.find_one({"username": username})
        if user is None:
            return False
        return True

    def get_top_flights(self):
        # 假设 flight_info_collection 是你的航班信息 collection
        top_flights = self.flight_info_collection.find().sort('seat_availability', -1).limit(6)
        # 将结果转换为列表，方便进一步操作
        top_flight_list = [{
            'flight_identifier': flight['flight_identifier'],
            'source_place': flight['source_place'],
            'destination_place': flight['destination_place'],
            'departure_time': datetime.strptime(flight['departure_time'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%dT%H:%M:%S') if isinstance(flight['departure_time'], str) else flight['departure_time'].strftime('%Y-%m-%dT%H:%M:%S'),
            'airfare': flight['airfare'],
            'seat_availability': flight['seat_availability']
        } for flight in top_flights]
        return json.dumps(top_flight_list)

if __name__ == '__main__':
    server = Server()
    server.start_listening()