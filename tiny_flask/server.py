import socket  
import threading
import time
from tiny_flask.response import Response
from tiny_flask.request import Request
# Reference https://docs.python.org/3/library/socket.html#module-socket

class HTTPServer:

    def __init__(self, port:int) -> None:

        self.server_socket = socket.create_server(("localhost", port), reuse_port=True)
        self.is_running = True
        self.client_thread_pool = dict()
        self.routes = []  # List of (method, path_pattern, handler)

        # Spawn a thread to accept client connections
        listen_thread = threading.Thread(target=self.listen, name="server_thread", args=(port,))
        listen_thread.start()

    def listen(self, port) -> None:
        self.log(f"Server listening on port {port} ... ")
        self.log(f"Server URL: http://localhost:{port}/")
        while self.is_running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.log(f"Accepted connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), name=f"client_thread_id{addr}")
                self.client_thread_pool[addr] = client_thread
                client_thread.start()
            except Exception as e:
                self.log(e)

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
        try:
            request = client_socket.recv(1024).decode()
            if not request:
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
