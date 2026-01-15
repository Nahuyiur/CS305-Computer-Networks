import socket, threading

class Echo(threading.Thread):
    def __init__(self, conn, address):
        threading.Thread.__init__(self)
        self.conn = conn
        self.address = address

    def run(self):
        # 每个线程独立执行run() 函数
        while True:
            data = self.conn.recv(2048)
            if data and data != b'exit':
                self.conn.send(data)
                print('{} sent: {}'.format(self.address, data))
            else:
                self.conn.close()
                return

def echo():
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 5555))
    sock.listen(10)
    while True:
        conn, address = sock.accept()
        Echo(conn, address).start()
        # 调用.start() 启动该线程(会自动执行 run())

if __name__ == "__main__":
    try:
        echo()
    except KeyboardInterrupt:
        pass
