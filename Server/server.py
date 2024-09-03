import json
import socket
import threading
from datetime import datetime, timedelta

from pymongo import MongoClient
from utils.data_process import binary_string_to_string


class Server:
    def __init__(self, config_file='../config.json',flag=0):
        print("Server: Server starting...")
        # 从 config.json 文件读取配置
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.host = config.get('host', 'localhost')
        if flag == 0:
            self.port = int(config.get('port', 12345))
        else:
            self.port = int(config.get('test_port', 12346))
        print(f"Server: Server ip: {self.host}:{self.port}")
        self.server_socket = None
        self.client_address = None
        self.monitor_dict = {}
        self.running = False
        try:
            self.connect_database(config_file=config_file, flag=flag)
        except Exception as e:
            print("Server: connect failed\n", str(e))

    def connect_database(self, flag: int = 0, config_file='../config.json'):
        # 从配置文件中获取MongoDB连接参数
        with open(config_file, 'r') as f:
            config = json.load(f)
        host = config['mongodb']['host']
        port = config['mongodb']['port']
        if flag == 0:
            database_name = config['mongodb']['database']
        else:
            database_name = config['mongodb']['test_database']
        username = config['mongodb']['username']
        password = config['mongodb']['password']

        # 连接到MongoDB
        if username and password:
            # 如果配置了用户名和密码，则使用身份验证连接
            mongo_uri = f"mongodb://{username}:{password}@{host}:{port}/{database_name}"
        else:
            # 否则使用无身份验证连接
            mongo_uri = f"mongodb://{host}:{port}/"
        client = MongoClient(mongo_uri)
        # 选择数据库
        db = client[database_name]
        # 选择集合
        self.collection = db[database_name]

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
                    if ret_flag == 0:
                        response = f"{ret_msg}"
                        print(f"Server: 发送给{self.client_address}的数据: {ret_msg}")
                        self.server_socket.sendto(response.encode('utf-8'), self.client_address)
                except socket.timeout:
                    # 超时检查，避免无限等待
                    continue
        except Exception as e:
            print("Server: start listening failed: " + str(e))
        finally:
            self.server_socket.close()
            print("Server: 服务器已关闭")

    def stop_listening(self):
        if not self.running:
            return
        self.running = False
        # 在关闭之前检查是否已经初始化
        if self.server_socket:
            self.server_socket.close()
        print("Server: 服务器已停止监听")

    def handle_request(self, data: str) -> (int, str):
        opt = data.split(';')[0]
        # 使用 getattr 从对象 obj 中获取方法
        method = getattr(self, opt, None)

        if callable(method):
            return method(data)
        else:
            return f"Method '{opt}' not found"


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
        self.collection.insert_one(flight_document)
        self.collection.create_index([("flight_identifier", 1)], unique=True)

    # 返回标志位(0:success, 1:fail) + 所有符合条件的航班信息/错误信息
    def query_flight(self, data: str) -> (int, str):
        try:
            source_place = data.split(';')[1]
            destination_place = data.split(';')[2]
            ret = []
            query = {
                "source_place": source_place,
                "destination_place": destination_place
            }
            projection = {
                "_id": 0
            }
            # 执行查询并应用投影
            cursor = self.collection.find(query, projection)
            # 将所有匹配的航班信息添加到返回列表中
            ret = [flight for flight in cursor]
            if len(ret) == 0:
                return 0, f"No flights matched {source_place} to {destination_place}!"
            return 0, ''.join([flight.__repr__() for flight in ret])
        except Exception as e:
            return 1, str(e)

    # 返回标志位(0:success, 1:fail) + 对应航班信息/错误信息
    def query_flight_info(self, data: str) -> (int, str):
        try:
            flight_identifier = int(data.split(';')[1])
            flight_info = self.collection.find_one(
                {
                    "flight_identifier": flight_identifier
                },
                projection = {
                    "_id": 0
                }
            )
            if flight_info:
                return 0, flight_info
            return 0, f"No flights matched {flight_identifier}!"
        except Exception as e:
            return 1, str(e)

    def reserve_seats(self, data: str) -> (int, str):
        try:
            # 解析传入的数据
            flight_identifier = int(data.split(';')[1])
            seats_count = int(data.split(';')[2])

            # 查找航班信息
            flight_info = self.collection.find_one({"flight_identifier": flight_identifier})
            # 检查座位数量是否足够
            if flight_info["seat_availability"] < seats_count:
                return 0, "Seats not enough!"
            else:
                # 更新座位数量
                new_seat_availability = flight_info["seat_availability"] - seats_count
                self.collection.update_one(
                    {"flight_identifier": flight_identifier},
                    {"$set": {"seat_availability": new_seat_availability}}
                )
                self.reserve_seats_callback(flight_identifier, new_seat_availability)
                return 0, "Seats reserved!"
        except Exception as e:
            return 1, str(e)

    def reserve_seats_callback(self, flight_identifier, new_seat_availability):
        if flight_identifier in self.monitor_dict:
            monitor_list = self.monitor_dict[flight_identifier]
            for monitor in monitor_list:
                if datetime.now() < monitor["end_time"]:
                    # todo 转为01串
                    response = f"seats' availability updates: {new_seat_availability}"
                    self.server_socket.sendto(response.encode('utf-8'), monitor["client_address"])

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

    # todo block requests if already exists a monitor
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

            for monitor in self.monitor_dict[flight_identifier]:
                if self.client_address == monitor["client_address"] and monitor["end_time"] > end_time:
                    return 0, "Monitoring already exists!"

            monitor_info = {
                "client_address": self.client_address,  # 假设 client_address 是在其他地方设置的
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
            print("error:" + str(e))
            return 1, str(e)

    def monitor_end_thread(self, flight_identifier: int, monitor_info: dict):
        # 等待监视期结束
        end_time = monitor_info["end_time"]
        time_to_wait = (end_time - datetime.now()).total_seconds()
        if time_to_wait > 0:
            threading.Event().wait(time_to_wait)

        # 发送监视结束消息
        client_address = monitor_info["client_address"]
        response = f"monitor finished"
        self.server_socket.sendto(response.encode('utf-8'), client_address)
        print(f"Server: {client_address} finished monitoring")
        # 从监视列表中移除
        self.monitor_dict[flight_identifier].remove(monitor_info)
        if not self.monitor_dict[flight_identifier]:
            del self.monitor_dict[flight_identifier]


if __name__ == "__main__":
    print(1)
