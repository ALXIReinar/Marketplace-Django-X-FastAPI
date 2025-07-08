import socket
import time


def wait_conn(host, port, timeout=10):
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            if time.time() - start > timeout:
                raise TimeoutError(f'Сервер не поднялся: {host}:{port}')
            time.sleep(0.2)