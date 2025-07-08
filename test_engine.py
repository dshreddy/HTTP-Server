import socket
import threading
import time
from http_server.server import HTTPServer

HOST = "localhost"
PORT = 4221

def start_server() -> None:
    server = HTTPServer(PORT)
    return server

def echo_end_point_test():
    # Manually create a socket and send raw HTTP request
    with socket.create_connection((HOST, PORT)) as sock:
        request = f"GET /echo/abc HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nUser-Agent: curl/7.64.1\r\nAccept: */*\r\n\r\n"
        sock.sendall(request.encode())

        # Receive the full response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        print(response.decode())

def user_agent_end_point_test():
    # Manually create a socket and send raw HTTP request
    with socket.create_connection((HOST, PORT)) as sock:
        request = f"GET /user-agent HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nUser-Agent: foobar/1.2.3\r\nAccept: */*\r\n\r\n"
        sock.sendall(request.encode())

        # Receive the full response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        print(response.decode())

def main():
    # Start Server
    server = start_server()
    time.sleep(1) 

    # Run Tests
    echo_end_point_test()
    user_agent_end_point_test()

    # Stop Server
    server.stop_server()

main()