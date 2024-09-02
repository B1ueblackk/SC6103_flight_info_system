from datetime import datetime

from Server.server import Server

if __name__ == '__main__':
    try:
        server = Server()
        server.start_listening()
    except Exception as e:
        print(str(e))