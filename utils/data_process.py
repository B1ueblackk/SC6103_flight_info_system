import struct
from datetime import datetime
from Server.flight import Flight


def marshall(flight: Flight) -> bytes:
    # 数据格式定义：
    #   - 4字节整数 (flight_identifier)
    #   - 字符串 (source_place) 前面是 4字节长度
    #   - 字符串 (destination_place) 前面是 4字节长度
    #   - 8字节浮点数 (airfare)
    #   - 4字节整数 (seat_availability)
    #   - 19字节日期时间 (departure_time 格式为 ISO 8601)

    # 格式化日期时间为 ISO 8601
    # 默认大端存储
    departure_time_str = flight.departure_time.strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')

    # 打包数据
    binary_data = struct.pack(
        '>I', flight.flight_identifier
    )
    binary_data += pack_string(flight.source_place)
    binary_data += pack_string(flight.destination_place)
    binary_data += struct.pack('>d', flight.airfare)
    binary_data += struct.pack('>I', flight.seat_availability)
    binary_data += struct.pack('19s', departure_time_str)

    return binary_data


def unmarshall(binary_data: bytes) -> Flight:
    # 使用网络字节序（大端序）
    flight_identifier = struct.unpack('>I', binary_data[:4])[0]
    binary_data = binary_data[4:]
    # print(f"After flight_identifier: {binary_data}")

    source_place, binary_data = unpack_string(binary_data)
    # print(f"After source_place: {binary_data}")

    destination_place, binary_data = unpack_string(binary_data)
    # print(f"After destination_place: {binary_data}")

    airfare = struct.unpack('>d', binary_data[:8])[0]
    binary_data = binary_data[8:]
    # print(f"After airfare: {binary_data}")

    seat_availability = struct.unpack('>I', binary_data[:4])[0]
    binary_data = binary_data[4:]
    # print(f"After seat_availability: {binary_data}")

    departure_time_str = struct.unpack('19s', binary_data[:19])[0].decode('utf-8')
    departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M:%S')

    return Flight(
        flight_identifier,
        source_place,
        destination_place,
        departure_time,
        airfare,
        seat_availability
    )


def pack_string(string: str) -> bytes:
    # 打包字符串长度（4字节整数）和字符串本身
    encoded_string = string.encode('utf-8')
    length = len(encoded_string)
    return struct.pack('I', length) + encoded_string

def unpack_string(binary_data: bytes) -> (str, bytes):
    # 解包字符串长度（4字节整数）和字符串本身
    length = struct.unpack('I', binary_data[:4])[0]
    string = binary_data[4:4 + length].decode('utf-8')
    return string, binary_data[4 + length:]

def bytes_to_binary_string(data: bytes) -> str:
    # 将每个字节转换为8位二进制，并连接成字符串
    return ''.join(format(byte, '08b') for byte in data)

def string_to_binary_string(data: str) -> str:
    return bytes_to_binary_string(data.encode('utf-8'))

def binary_string_to_string(binary_string: str) -> str:
    # 按8位分割二进制字符串
    chars = [binary_string[i:i + 8] for i in range(0, len(binary_string), 8)]
    # 将每个8位二进制数转换为对应的字符
    text = ''.join([chr(int(char, 2)) for char in chars])
    return text


if __name__ == '__main__':
    # departure_time = datetime(2024, 9, 1, 15, 30)  # 示例：2024年9月1日15:30
    # flight = Flight(
    #     flight_identifier=101,
    #     source_place="New York",
    #     destination_place="Los Angeles",
    #     departure_time=departure_time,
    #     airfare=299.99,
    #     seat_availability=50
    # )
    # binary_data = marshall(flight)
    # print(binary_data)
    # flight1 = unmarshall(binary_data)
    # print(flight1.__repr__())
    print(binary_string_to_string("0100111001100101011101110010000001011001011011110111001001101011"))
    print(bytes_to_binary_string(b'New York'))