from multiprocessing import Process
import os
# import dotenv
# dotenv.load_dotenv("local.env")

def run_app1():
    os.system("python3 ./Client/server.py")


def run_app2():
    os.system("python3 ./Server/server.py")


if __name__ == "__main__":
    # 创建两个进程，分别启动两个 Flask 应用
    p1 = Process(target=run_app1)
    p2 = Process(target=run_app2)

    # 启动两个进程
    p1.start()
    p2.start()

    # 等待两个进程结束
    p1.join()
    p2.join()