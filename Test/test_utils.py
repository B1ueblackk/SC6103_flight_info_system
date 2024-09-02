import unittest
from datetime import datetime

import utils.data_process
from Server.flight import Flight


class TestUtils(unittest.TestCase):
    def setUp(self):
        # 在每个测试方法执行前调用
        print("Testing utils...")

    def test_marshall_and_unmarshall(self):
        departure_time = datetime(2024, 9, 1, 15, 30)  # 示例：2024年9月1日15:30
        flight = Flight(
            flight_identifier=101,
            source_place="New York",
            destination_place="Los Angeles",
            departure_time=departure_time,
            airfare=299.99,
            seat_availability=50
        )
        binary_data = utils.data_process.marshall(flight)
        self.assertEqual(
            binary_data,
            b'\x00\x00\x00e\x08\x00\x00\x00New York\x0b\x00\x00\x00Los Angeles@r\xbf\xd7\n=p\xa4\x00\x00\x0022024-09-01T15:30:00'
        )
        self.assertEqual(
            utils.data_process.unmarshall(binary_data).__repr__(), flight.__repr__())

    def test_bytes_to_binary_string(self):
        self.assertEqual(
            utils.data_process.bytes_to_binary_string(b'\x00\x00\x00e\x08\x00\x00\x00New York'),
            "00000000000000000000000001100101000010000000000000000000000000000100111001100101011101110010000001011001011011110111001001101011")

    def test_binary_string_to_string(self):
        self.assertEqual(
            utils.data_process.binary_string_to_string("0100111001100101011101110010000001011001011011110111001001101011"),
            "New York")

if __name__ == '__main__':
    unittest.main()
