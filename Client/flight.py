from datetime import datetime

class Flight:
    def __init__(self, flight_identifier, source_place, destination_place, departure_time, airfare, seat_availability):
        self.flight_identifier = flight_identifier
        self.source_place = source_place
        self.destination_place = destination_place
        self.departure_time = departure_time
        self.airfare = airfare
        self.seat_availability = seat_availability

    def __repr__(self):
        """
        返回 Flight 类实例的字符串表示
        """
        return (f"Flight(flight_identifier={self.flight_identifier}, "
                f"source_place='{self.source_place}', "
                f"destination_place='{self.destination_place}', "
                f"departure_time={self.departure_time}, "
                f"airfare={self.airfare}, "
                f"seat_availability={self.seat_availability})")

# 示例用法
if __name__ == "__main__":
    # 创建一个 Flight 实例
    departure_time = datetime(2024, 9, 1, 15, 30)  # 示例：2024年9月1日15:30
    flight = Flight(
        flight_identifier=101,
        source_place="New York",
        destination_place="Los Angeles",
        departure_time=departure_time,
        airfare=299.99,
        seat_availability=50
    )

    # 打印 Flight 实例
    print(flight)
