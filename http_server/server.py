import socket  
import threading
import time
# Reference https://docs.python.org/3/library/socket.html#module-socket

class HTTPServer:

    def __init__(self, port:int) -> None:

        self.server_socket = socket.create_server(("localhost", port), reuse_port=True)
        self.is_running = True
        self.client_thread_pool = dict()

        # Spawn a thread to accept client connections
        listen_thread = threading.Thread(target=self.listen, name="server_thread")
        listen_thread.start()

    def listen(self) -> None:

        self.log("Server listening on port 4221 ... ")
        while self.is_running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.log(f"Accepted connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), name=f"client_thread_id{addr}")
                self.client_thread_pool[addr] = client_thread
                client_thread.start()
            except Exception as e:
                self.log(e)

    def handle_client(self, client_socket: socket.socket) -> None:
        try:
            request = client_socket.recv(1024).decode()
            if not request:
                return  # No data received, close the connection

            request_parts = request.split('\r\n')
            http_method, target, http_version = request_parts[0].split(' ')
            headers = dict()
            for line in request_parts[1:]:
                if line == "":
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    # Header names are case-insensitive.
                    key = key.strip().lower()
                    headers[key] = value.strip() 

            if target == "/":
                response = b"HTTP/1.1 200 OK\r\n\r\n"
            elif target == "/user-agent":
                if "user-agent" in headers:
                    response_body = headers["user-agent"]
                    content_length = len(response_body)
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {content_length}\r\n"
                        "\r\n"
                        f"{response_body}"
                    ).encode()
                else:
                    response = b"HTTP/1.1 404 Bad Request\r\n\r\n"
            elif target.startswith("/echo/"):
                response_body = target[6:]
                content_length = len(response_body)
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {content_length}\r\n"
                    "\r\n"
                    f"{response_body}"
                ).encode()
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

            client_socket.sendall(response)
        except Exception as e:
            self.log(f"Exception: {e}")
        finally:
            client_socket.close()

    def stop_server(self) -> None:
        self.is_running = False
        #TODO:Close client threads & sockets properly before closing the server socket
        self.server_socket.close()
        self.log("Server stopped.")
    
    def log(self, message: str) -> None:
        current_thread = threading.current_thread().name
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{current_thread}] {message}", flush=True)
