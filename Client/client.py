import json
import socket

from utils.data_process import string_to_binary_string


class Client:
    def __init__(self, config_file='../config.json', flag=0):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.server_host = config.get('host', 'localhost')
        if flag == 0:
            self.server_port = int(config.get('port', 12345))
        else:
            self.server_port = int(config.get('test_port', 12346))

    def query_flight(self, source_place: str, destination: str):
        query_str = "query_flight" + ";" + source_place + ";" + destination
        return self.send_request(query_str)

    def query_flight_info(self, flight_id: int):
        query_str = "query_flight_info" + ";" + str(flight_id)
        return self.send_request(query_str)

    def reserve_seats(self, flight_id: int, seats_count: int):
        transfer_str = "reserve_seats" + ";" + str(flight_id) + ";" + str(seats_count)
        return self.send_request(transfer_str)

    def monitor_update(self, flight_id: int, period_time: int):
        transfer_str = "monitor_update" + ";" + str(flight_id) + ";" + str(period_time)
        self.send_request(transfer_str)

    def send_request(self, data: str):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        binary_data = string_to_binary_string(data)
        try:
            # todo 01
            client.sendto(binary_data.encode('utf-8'), (self.server_host, self.server_port))
            print(data)
            if data.startswith("monitor_update"):
                while True:
                    response, _ = client.recvfrom(1024)
                    response_text = response.decode('utf-8')
                    print(f"从服务器接收到的响应: {response_text}")
                    # todo 01
                    if response_text.startswith("monitor finished"):
                        break
            else:
                response, _ = client.recvfrom(1024)
                print(f"从服务器接收到的响应: {response.decode('utf-8')}")
                return 0, response.decode()
        except socket.timeout:
            return 1, "Request timed out"
        except Exception as e:
            return 1, print(str(e))
        finally:
            # 关闭 socket
            client.close()


if __name__ == "__main__":
    test_client = Client()
    # test_client.query_flight("Beijin", "Los Angeles")
    response = test_client.query_flight_info(101)
