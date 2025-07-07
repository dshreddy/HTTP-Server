import socket  
import threading
# Reference https://docs.python.org/3/library/socket.html#module-socket

def start_server() -> None:
    '''
        args: None
        returns: None
    '''
    global server_socket
    # Convenience function which creates a TCP socket bound to address (a 2-tuple (host, port)) and returns the socket object.
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True) 
    print("Server listening on port 4221 ... ")

def accept_clients() -> None:
    '''
        args: None
        returns: None
    '''
    while True:
        client_socket, addr = server_socket.accept()
        '''
            Accept a connection. 
            The socket must be bound to an address and listening for connections. 
            The return value is a pair (conn, address) 
            where conn is a new socket object usable to send and receive data on the connection, 
            and address is the address bound to the socket on the other end of the connection.
        '''
        print(f"Accepted connection from {addr}")
        # Spawn a thread to handle this client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, ))
        client_thread.start()

def handle_client(client_socket: socket) -> None:
    '''
        args: 
                client_socket (Type: socket)
    '''
    request = client_socket.recv(1024)
    print("Received request:")
    print(request.decode())
    
    response = b"HTTP/1.1 200 OK\r\n\r\n"
    client_socket.sendall(response)
    client_socket.close()

def stop_server():
    server_socket.close()
    print("Server stopped.")

def main():

    start_server()
    thread_for_listening = threading.Thread(target=accept_clients, args=())
    thread_for_listening.start()
    
    while True:
        command = input()
        if command == "q":
            stop_server()
            break
        

if __name__ == "__main__":
    main()
