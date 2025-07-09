import socket  
import threading
import time
import inspect
from tiny_flask.response import Response
from tiny_flask.request import Request
# Reference https://docs.python.org/3/library/socket.html#module-socket

COLOR_RESET = "\033[0m"
INFO = "\033[94m"     # Blue
SUCCESS = "\033[92m",  # Green
WARNING = "\033[93m",  # Yellow
ERROR = "\033[91m",    # Red
DEBUG = "\033[90m",    # Gray

class HTTPServer:

    def __init__(self, port:int) -> None:

        self.server_socket = socket.create_server(("localhost", port), reuse_port=True)
        self.is_running = True
        self.routes = []  # List of (method, path_pattern, handler)
        self.client_time_out = 120 # 2 minutes timeout
        self.client_threads = {}
        self.client_sockets = {}
        # Spawn a thread to accept client connections
        accept_thread = threading.Thread(target=self.accept, name="accept_thread", args=(port,))
        accept_thread.start()
        # Spawn a thread to listen for user input
        input_thread = threading.Thread(target=self.user_input, name="input_thread")
        input_thread.start()
    
    def user_input(self):
        self.log("Press 'q' to stop the server.", level="INFO")
        while True:
            line = input()
            if line == "q":
                self.stop_server()
                break

    def accept(self, port) -> None:
        self.log(f"Server listening on port {port} ... ", level="SUCCESS")
        self.log(f"Server URL: http://localhost:{port}/", level="SUCCESS")
        while self.is_running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.log(f"Accepted connection from {addr}", level="SUCCESS")
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket,),
                    name=f"client_thread {addr}",
                    )
                client_thread.start()
                self.client_threads[addr] = client_thread
                self.client_sockets[addr] = client_socket
            except ConnectionAbortedError:
                pass # This happened because we closed the server_socket in input_thread while it's being used in the server_thread for accepting clients which is a blocked call 
            except Exception as e:
                self.log(e, level="ERROR")

    def route(self, path_pattern: str, methods=["GET"]):
        def decorator(func):
            for method in methods:
                self.routes.append((method.upper(), path_pattern, func))
            return func
        return decorator

    def match_route(self, method, path):
        for route_method, pattern, handler in self.routes:
            if method != route_method:
                continue

            path_parts = path.strip("/").split("/")
            pattern_parts = pattern.strip("/").split("/")

            if len(path_parts) != len(pattern_parts):
                continue

            path_params = {}
            matched = True

            for p_seg, pt_seg in zip(path_parts, pattern_parts):
                if pt_seg.startswith("{") and pt_seg.endswith("}"):
                    param_name = pt_seg[1:-1]
                    path_params[param_name] = p_seg
                elif p_seg != pt_seg:
                    matched = False
                    break

            if matched:
                return handler, path_params

        return None, None
    
    def parse_request(self, request: str) -> Request:
        request_parts = request.split('\r\n')
        # Request line
        method, target, http_version = request_parts[0].split(' ')
        obj = Request(method= method, target= target, version= http_version)

        # Headers
        for i in range(1, len(request_parts)):
            header = request_parts[i]
            if ":" in header:
                key, value = header.split(":", 1)
                key = key.strip().lower() # Header names are case-insensitive.
                obj.headers[key] = value.strip()
            else:
                # Request body
                while i < len(request_parts):
                    obj.body += request_parts[i]
                    i += 1
                break
        return obj

    def handle_client(self, client_socket: socket.socket) -> None:
        # By default, HTTP/1.1 connections are persistent, meaning the same TCP connection can be reused for multiple requests.
        client_socket.settimeout(self.client_time_out)  
        while self.is_running:
            try:
                request = client_socket.recv(1024).decode()
                if not request:
                    self.log(f"Client {client_socket.getpeername()} closed connection", level="WARNING")
                    return  # No data received, close the connection
                
                request = self.parse_request(request)
                handler, path_params = self.match_route(request.method.upper(), request.target)
                response = Response()

                if handler:
                    result = handler(request, **path_params)
                    if isinstance(result, str):
                        response.body = result
                    elif isinstance(result, Response):
                        response = result
                    else:
                        response.status_code = "500"
                        response.reason = "Server Error"
                        response.body = f"500 `{handler}` returned invalid type, expected (str || Response)"
                else:
                    response.status_code = "404"
                    response.reason = "Not Found"
                    response.body = f"404 No handler found for `({request.method}, {request.target})`"
                
                # Override HTTP version to what we received in request
                response.http_version = request.http_version
                
                # Only add the content type here if not done in handler
                if "content-type" not in response.headers:
                            response.add_header("Content-Type", "text/plain")

                # Support gzip compression if mentioned in request
                if "accept-encoding" in request.headers:
                    acceptable_encodings = request.headers["accept-encoding"].split(', ')
                    if "gzip" in acceptable_encodings:
                        response.compress()

                # Override content length for correctness
                response.add_header("Content-Length", str(len(response.body)))

                # Send the reponse
                client_socket.sendall(response.get())

                if "connection" in request.headers:
                    close = (request.headers["connection"] == "close")
                    if close:
                        self.log(f"{client_socket.getpeername()}: Closed connection since `Connection: close` header is there in request", level="WARNING")
                        break
            except socket.timeout:
                self.log(f"{client_socket.getpeername()}: Closed connection due to {self.client_time_out} seconds of inactivity", level="WARNING")
                break  # Exit loop, close connection
            except Exception as e:
                self.log(f"{e}", level="ERROR")
                break

        # Delete the thread and socket from thread pool and socket pool
        addr = client_socket.getpeername()
        self.client_threads.pop(addr)
        self.client_sockets.pop(addr)

        try:
            client_socket.close()
        except Exception as e:
            pass # Socket is already closed

    def stop_server(self) -> None:
        self.is_running = False
        self.log("Stopping server and closing all client connections...", level="WARNING")

        # Close all client sockets to unblock recv()
        for addr, sock in list(self.client_sockets.items()):
            try:
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
            except Exception:
                pass
        
        # Wait for all client threads to finish
        for addr, thread in list(self.client_threads.items()):
            if thread.is_alive():
                thread.join(timeout=2)

        try:
            self.server_socket.close()
        except Exception:
            pass

        self.log("Server stopped.", level="SUCCESS")
    
    def log(self, message: str, level: str = "INFO") -> None:
        COLOR_RESET = "\033[0m"
        COLOR_MAP = {
            "INFO": "\033[94m",     # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",    # Red
            "DEBUG": "\033[90m",    # Gray
        }
        color = COLOR_MAP.get(level.upper(), "")
        current_thread = threading.current_thread().name
        caller = inspect.stack()[1]
        filename = caller.filename
        line_number = caller.lineno
        caller_name = caller.function
        # print(f"{color}[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Thread : {current_thread}] [{caller_name} @ {filename}:{line_number}] {message}", flush=True)
        print(f"{color}[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{current_thread}] {message}", flush=True)

