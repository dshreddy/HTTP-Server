import socket  # noqa: F401


def main():
    # Create a server socket on bind it to port 4221
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    # Wait for client connections
    server_socket.accept() 


if __name__ == "__main__":
    main()
