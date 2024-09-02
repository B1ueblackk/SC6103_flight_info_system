import json
import socket

from Server.utils.data_process import marshall, pack_string, string_to_binary_string


class TestClient(object):
    def __init__(self, config_file='../Server/config.json'):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.server_host = config.get('host', 'localhost')
        self.server_port = int(config.get('port', 12345))

    def query_flight(self, source_place: str, destination: str):
        query_str = "query_flight" + ";" + source_place + ";" + destination
        self.send_request(query_str)

    def query_flight_info(self, flight_id: int):
        query_str = "query_flight_info" + ";" + str(flight_id)
        self.send_request(query_str)

    def reserve_seats(self, flight_id: int, seats_count: int):
        transfer_str = "reserve_seats" + ";" + str(flight_id) + ";" + str(seats_count)
        self.send_request(transfer_str)

    def monitor_update(self, flight_id: int):
        transfer_str = "monitor_update" + ";" + str(flight_id)
        self.send_request(transfer_str)

    def send_request(self, data: str):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = string_to_binary_string(data)
        try:
            client.sendto(data.encode('utf-8'), (self.server_host, self.server_port))
            response, _ = client.recvfrom(1024)
            print(f"从服务器接收到的响应: {response.decode('utf-8')}")
        except Exception as e:
            print(str(e))
        finally:
        # 关闭 socket
            client.close()



if __name__ == "__main__":
    test_client = TestClient()
    test_client.query_flight("beijing", "la")
