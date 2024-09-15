from flask import Flask
from Server.server import Server

app = Flask(__name__)

server = Server()
server.start_listening()

if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5001)
    except Exception as e:
        print(str(e))