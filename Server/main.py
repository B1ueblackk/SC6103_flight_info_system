from datetime import datetime

from Server.server import Server

if __name__ == '__main__':
    try:
        server = Server()
        server.add_flight(
            flight_identifier=102,
            source_place="Beijing",
            destination_place="Los Angeles",
            departure_time=datetime(2024, 11, 1, 19, 30),
            airfare=299.99,
            seat_availability=56)
        server.start_listening()
    except Exception as e:
        print(str(e))