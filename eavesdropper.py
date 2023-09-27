import socket
import sys

import utils

def drop_the_eaves():
    if len(sys.argv) < 2:
        sys.exit(1)

    client_port = ''
    server_port = ''
    spy_path = ''
    with open(sys.argv[1], mode='r', encoding='utf-8') as f:
        for line in f:
            line = line.strip('\n').split('=')
            if line[0] == "client_port":
                client_port = line[1]
            elif line[0] == "server_port":
                server_port = line[1]
            elif line[0] == "spy_path":
                spy_path = line[1]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_sock.bind(('localhost', int(client_port)))
        client_sock.listen()
        client_connection, client_address = client_sock.accept()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            try:
                server_sock.connect(('localhost', int(server_port)))
            except:
                print(f"AS: Cannot establish connection\r\n", flush=True, end='')
                sys.exit(3)

            from_blank_cont = []
            to_blank_cont = []
            body_cont = []
            is_authed = False
            is_reading_body = False

            while client_connection:
                while True:
                    server_response = server_sock.recv(1024)

                    raw_server_response = server_response.decode('utf-8', errors='ignore').strip('\r\n')
                    if raw_server_response.endswith("250 AUTH CRAM-MD5"):
                        raw_server_response = raw_server_response.split("\r\n")
                        print(f"S: {raw_server_response[0]}\r\n", flush=True, end='')
                        print(f"S: {raw_server_response[1]}\r\n", flush=True, end='')
                        print(f"AC: {raw_server_response[0]}\r\n", flush=True, end='')
                        print(f"AC: {raw_server_response[1]}\r\n", flush=True, end='')
                    else:
                        print(f"S: {raw_server_response}\r\n", flush=True, end='')
                        print(f"AC: {raw_server_response}\r\n", flush=True, end='')

                    client_connection.sendall(server_response)

                    client_response = client_connection.recv(1024)
                    raw_client_response = client_response.decode('utf-8', errors='ignore').strip('\r\n')

                    print(f"C: {raw_client_response}\r\n", flush=True, end='')
                    print(f"AS: {raw_client_response}\r\n", file=sys.stdout, flush=True, end='')

                    if is_reading_body:
                        if raw_client_response == ".":
                            is_reading_body = False
                            utils.txt_composer(from_blank_cont, to_blank_cont, body_cont, str(utils.get_path(spy_path)), is_authed)
                        else:
                            body_cont.append(raw_client_response)
                    elif raw_client_response.startswith("MAIL FROM:"):
                        from_blank_cont = from_handler(from_blank_cont, raw_client_response)
                    elif raw_client_response.startswith("RCPT TO:"):
                        to_blank_cont = to_handler(to_blank_cont, raw_client_response)
                    elif raw_client_response == "DATA":
                        is_reading_body = True
                    elif raw_client_response == "QUIT":
                        quit_handler(server_sock, client_connection, client_response)
                        sys.exit(0)

                    server_sock.sendall(client_response)


def from_handler(from_blank_cont, raw_client_response):
    from_blank_cont.append(raw_client_response[10:])
    return from_blank_cont


def to_handler(to_blank_cont, raw_client_response):
    to_blank_cont.append(raw_client_response[8:])
    return to_blank_cont


def quit_handler(server_sock, client_connection, client_response):
    server_sock.sendall(client_response)
    server_response = server_sock.recv(1024)
    raw_server_response = server_response.decode('utf-8', errors='ignore').strip('\r\n')
    print(f"S: {raw_server_response}\r\n", flush=True, end='')
    print(f"AC: {raw_server_response}\r\n", flush=True, end='')

    client_connection.sendall(server_response)


if __name__ == "__main__":
    drop_the_eaves()