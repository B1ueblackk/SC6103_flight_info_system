from Client.app import Client

if __name__ == '__main__':
    client = Client()
    client.send_request("reserve_seats;101;2")