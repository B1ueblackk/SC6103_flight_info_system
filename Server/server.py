import json
import socket
from datetime import datetime, timedelta

from pymongo import MongoClient
from Server.utils.data_process import binary_string_to_string


class Server:
    def __init__(self, config_file='config.json'):
        print("Server starting...")
        # 从 config.json 文件读取配置
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.host = config.get('host', 'localhost')
        self.port = int(config.get('port', 12345))
        print(f"Server ip: {self.host}:{self.port}")
        self.server_socket = None
        self.client_address = None
        self.monitor_dict = {}
        # 从配置文件中获取MongoDB连接参数
        host = config['mongodb']['host']
        port = config['mongodb']['port']
        database_name = config['mongodb']['database']
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
        self.collection = db['flight_info']

    def start_listening(self):
        # AF_INET代表ipv4，SOCK_DGRAM代表使用UDP作为通讯协议
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 监听config中对应的端口
        self.server_socket.bind((self.host, self.port))
        print(f"UDP 服务器已启动，正在监听 {self.host}:{self.port}...")

        try:
            while True:
                # 等待接收数据，1024为缓冲区大小
                data, self.client_address = self.server_socket.recvfrom(1024)
                text = binary_string_to_string(data.decode('utf-8'))
                print(f"接收到来自 {self.client_address} 的数据: {text}")
                ret_flag, ret_msg = self.handle_request(binary_string_to_string(data.decode('utf-8')))
                print(ret_msg)
                if ret_flag == 0:
                    # todo 转为01串
                    response = f"{ret_msg}"
                    self.server_socket.sendto(response.encode('utf-8'), self.client_address)
        except KeyboardInterrupt:
            self.server_socket.close()
            print("服务器已关闭")
        except Exception as e:
            print(str(e))

    def handle_request(self, data: str) -> (int, str):
        opt = data.split(';')[0]
        # 使用 getattr 从对象 obj 中获取方法
        method = getattr(self, opt, data)

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

            # 添加用户监听请求，包括监听的结束时间
            self.monitor_dict[flight_identifier].append({
                "client_address": self.client_address,  # 假设 client_address 是在其他地方设置的
                "end_time": end_time
            })
            return 0, "Monitoring started!"
        except Exception as e:
            return 1, str(e)



if __name__ == "__main__":
    print(1)
