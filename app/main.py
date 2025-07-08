import socket  
import threading
import time
# Reference https://docs.python.org/3/library/socket.html#module-socket

class HTTPServer:
    def __init__(self, port:int) -> None:
        self.server_socket = socket.create_server(("localhost", port), reuse_port=True) 
        self.client_thread_pool = dict()

    def listen(self) -> None:
        self.log("Server listening on port 4221 ... ")
        while True:
            client_socket, addr = self.server_socket.accept()
            self.log(f"Accepted connection from {addr}")
            # Spawn a thread to handle this client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, ))
            # Store the thread in the thread pool
            self.client_thread_pool[addr] = client_thread
            # Start the thread
            client_thread.start()
    
    def handle_client(self, client_socket: socket) -> None:

        while True:
            request = client_socket.recv(1024)
            request = request.decode()

            request_parts = request.split('\r\n')
            http_method, target, http_version = request_parts[0].split(' ')
            host = request_parts[1]
            user_agent = request_parts[2]
            accept = request_parts[3]
            request_body = request_parts[5]

            if target == "/":
                response = b"HTTP/1.1 200 OK\r\n\r\n"
            elif target.startswith("/echo/"):
                response_body = target[6:]
                content_length = len(response_body)
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {content_length}\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                response = response.encode()
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"
            client_socket.sendall(response)
        client_socket.close()

    def stop_server(self) -> None:
        #TODO:Close client threads & sockets properly before closing the server socket
        self.server_socket.close()
        print("Server stopped.")
    
    def log(self, message: str) -> None:
        print(f"[{time.time}] {message}")

def main():
    server = HTTPServer(port=4221)
    server.listen()
        
if __name__ == "__main__":
    main()
