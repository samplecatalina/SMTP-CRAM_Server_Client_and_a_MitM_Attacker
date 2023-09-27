import os
import sys
import socket
import signal

import server
import utils


def queue_processor(sock, server_inbox_path):
    loc_in_queue = 1
    while True:
        sock.listen()
        client_sock, unused_address = sock.accept()
        child_pid = os.fork()
        if child_pid == 0:
            server.connector(client_sock, server_inbox_path, os.getpid(), loc_in_queue)
        else:
            loc_in_queue += 1


def run():
    if len(sys.argv) < 2:
        sys.exit(1)

    server_port = ''
    inbox_path = ''
    with open(sys.argv[1], mode='r', encoding='utf-8') as f:
        for line in f:
            line = line.strip('\n').split('=')
            if line[0] == "server_port":
                server_port = line[1]
            elif line[0] == "inbox_path":
                inbox_path = line[1]


    server_inbox_path = str(utils.get_path(inbox_path))

    signal.signal(signal.SIGINT, exiter)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('localhost', int(server_port)))
    except:
        sys.exit(2)

    queue_processor(sock, server_inbox_path)


def exiter():
    sys.exit(0)


if __name__ == '__main__':
    run()