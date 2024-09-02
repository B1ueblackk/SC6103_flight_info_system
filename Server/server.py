import json
import socket
from datetime import datetime

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
                data, client_address = self.server_socket.recvfrom(1024)
                text = binary_string_to_string(data.decode('utf-8'))
                print(f"接收到来自 {client_address} 的数据: {text}")
                ret_flag, ret_msg = self.handle_request(binary_string_to_string(data.decode('utf-8')))
                if ret_flag == 0:
                    response = f"{ret_msg}"
                    self.server_socket.sendto(response.encode('utf-8'), client_address)
        except KeyboardInterrupt:
            self.server_socket.close()
            print("服务器已关闭")
        except Exception as e:
            print(str(e))

    def handle_request(self, data: str) -> str:
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


    def query_flight(self, data: str) -> (int, str):
        try:
            source_place = data.split(';')[1]
            destination_place = data.split(';')[2]
            ret = []
            for flight in self.collection:
                if flight.source_place == source_place and flight.destination_place == destination_place:
                    ret.append(flight)
            if len(ret) == 0:
                return 0, "No flights matched!"
            return 0, ''.join([flight.__repr__() for flight in ret])
        except Exception as e:
            return 1, str(e)

if __name__ == "__main__":
    print(1)
