import json
import threading
import time
import unittest
from http.client import responses

from Client.app import Client
from Server.server import Server


class TestServer(unittest.TestCase):
    def setUp(self):
        self.server_thread = threading.Thread(target=self.setup_and_start_server)
        self.server_thread.start()
        time.sleep(1)

    def tearDown(self):
        self.server.stop_listening()
        self.server_thread.join()

    def setup_and_start_server(self):
        self.server = Server(config_file='../config.json', flag=1)
        self.server.flight_info_collection.drop()
        self.server.start_listening()

    # 初始化测试数据库
    def add_data(self):
        with open('test_dataset.json', 'r') as f:
            config = json.load(f)
        for item in config:
            self.server.add_flight(
                flight_identifier=config[item]['flight_identifier'],
                source_place=config[item]['source_place'],
                destination_place=config[item]['destination_place'],
                departure_time=config[item]['departure_time'],
                airfare=config[item]['airfare'],
                seat_availability=config[item]['seat_availability']
            )

    # 测试数据库CRUD
    def test_database_CRUD(self):
        self.assertEqual(self.server.flight_info_collection.find_one(), None)
        self.add_data()

        flight101 = self.server.flight_info_collection.find_one({"flight_identifier":101})
        self.assertNotEqual(flight101, None)
        self.assertEqual(flight101["airfare"], 299.99)
        self.assertEqual(flight101["seat_availability"], 50)

    # 测试客户端与服务器连接
    def test_server_connection(self):
        self.add_data()
        thread_done = threading.Event()
        thread_result = {}

        def client_thread_func():
            test_client = Client(config_file='../config.json', flag=1)
            response_code, response_data = test_client.query_flight_info(101)
            thread_result['response_code'] = response_code
            thread_result['response_data'] = response_data
            thread_done.set()

        client_thread = threading.Thread(target=client_thread_func)
        client_thread.start()
        thread_done.wait()

        self.assertEqual(thread_result['response_code'], 0)
        self.assertIn("New York", thread_result['response_data'])

        client_thread.join()
        # 在客户端线程结束后立即停止服务器
        self.server.stop_listening()

    # 测试客户端监控(持续1min)
    def test_client_monitor(self):
        self.add_data()
        thread_done = threading.Event()
        thread_result = {}
        def client_thread_monitor():
            test_client = Client(config_file='../config.json', flag=1)
            response_code, response_data = test_client.monitor_update(101, 1)

        def client_thread_reserver():
            test_client = Client(config_file='../config.json', flag=1)
            response_code, response_data = test_client.reserve_seats(101, 2)

    def test_monitor_and_reserve_seats(self):
        self.add_data()

        monitor_done = threading.Event()
        reserve_done = threading.Event()
        monitor_result = {"received_updates": []}
        reserve_result = {"received_updates": []}

        def monitor_thread_func():
            test_client = Client(config_file='../config.json', flag=1)
            test_client.monitor_update(101, 1, monitor_result)
            monitor_done.set()

        def reserve_thread_func():
            reserve_done.wait()
            test_client = Client(config_file='../config.json', flag=1)
            for _ in range(11):  # 多次执行reserve_seats操作
                test_client.reserve_seats(101, 5, reserve_result)
                time.sleep(2)  # 每次预定操作之间间隔2秒
            test_client.client.close()

        # 启动监视线程
        monitor_thread = threading.Thread(target=monitor_thread_func)
        monitor_thread.start()
        print("Monitor thread started")

        # 启动占座线程
        reserve_thread = threading.Thread(target=reserve_thread_func)
        reserve_thread.start()

        time.sleep(0.5)
        reserve_done.set()

        print("Reserve thread started")

        # 等待占座操作完成
        reserve_thread.join()
        print("Reserve operation completed")

        # 等待监视操作完成
        monitor_done.wait()
        print("Monitor operation completed")

        self.assertEqual(
            monitor_result['received_updates'],
            ['Monitoring started!',
             "seats' availability updates: 45",
             "seats' availability updates: 40",
             "seats' availability updates: 35",
             "seats' availability updates: 30",
             "seats' availability updates: 25",
             "seats' availability updates: 20",
             "seats' availability updates: 15",
             "seats' availability updates: 10",
             "seats' availability updates: 5",
             "seats' availability updates: 0",
             'monitor finished']

        )
        self.assertEqual(reserve_result['received_updates'][-1], "Seats not enough!")
        self.assertEqual(reserve_result['received_updates'][-2], "Seats reserved!")
        # 等待线程结束
        monitor_thread.join()

if __name__ == '__main__':
    unittest.main()
