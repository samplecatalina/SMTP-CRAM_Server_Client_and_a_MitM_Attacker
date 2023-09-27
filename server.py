import os
import re
import signal
import socket
import sys
import hmac
import secrets
import base64
import utils

PERSONAL_ID = "764BFC"
PERSONAL_SECRET = "a69e820263d9dcfd4aceebb02bcd5f71"

server_msg_dict = {220: "220 Service ready",
                   221: "221 Service closing transmission channel",
                   235: "235 Authentication successful",
                   250: "250 Requested mail action okay completed",
                   334: "334 Server BASE64-encoded challenge",
                   354: "354 Start mail input end <CRLF>.<CRLF>",
                   421: "421 Service not available, closing transmission channel",
                   500: "500 Syntax error, command unrecognized",
                   501: "501 Syntax error in parameters or arguments",
                   503: "503 Bad sequence of commands",
                   504: "504 Unrecognized authentication type",
                   535: "535 Authentication credentials invalid"}


def sigint_trigger(sock, pid, loc_in_queue):
    if str(pid).isdigit() and str(loc_in_queue).isdigit():
        print(f"[{pid}][{loc_in_queue}]S: SIGINT received, closing\r\n", flush=True, end='')
    else:
        print(f"S: SIGINT received, closing\r\n", flush=True, end='')

    sock.sendall((server_msg_dict[421] + '\r\n').encode())

    if str(pid).isdigit() and str(loc_in_queue).isdigit():
        print(f"[{pid}][{loc_in_queue}]S: {server_msg_dict[421]}\r\n", flush=True, end='')
    else:
        print(f"S: {server_msg_dict[421]}\r\n", flush=True, end='')

    sock.close()
    sys.exit(0)


def tackle_mail_starting(from_blank_cont, to_blank_cont, body_cont, client_response):

    is_mail_issued = False
    if re.compile(utils.FROM_FORMAT).match(client_response):
        server_response = server_msg_dict[250]
        source_addr = re.compile(utils.FROM_FORMAT).search(client_response).group(2)
        from_blank_cont.clear()
        from_blank_cont.append(source_addr)
        to_blank_cont.clear()
        body_cont.clear()

        is_mail_issued = True
    elif client_response.startswith(("MAIL", "MAIL ")):
        server_response = server_msg_dict[501]
    else:
        server_response = server_msg_dict[500]

    return [server_response, from_blank_cont, to_blank_cont, body_cont, is_mail_issued]


def tackle_rcpt_starting(is_rcpt_issued, to_blank_cont, client_response):
    if re.compile(utils.RCPT_FORMAT).match(client_response):
        server_response = server_msg_dict[250]
        destination_addr = re.compile(utils.RCPT_FORMAT).search(client_response).group(2)
        to_blank_cont.append(destination_addr)
        is_rcpt_issued = True
    elif client_response.startswith(("RCPT", "RCPT ")) or \
            any(x in client_response for x in (' ', '\t')):
        server_response = server_msg_dict[501]
    else:
        server_response = server_msg_dict[500]

    return [is_rcpt_issued, to_blank_cont, server_response]


def tackle_data_starting(is_ehlo_issued, is_mail_issued, is_rcpt_issued, is_data_issued, client_response):
    if is_ehlo_issued and is_mail_issued and is_rcpt_issued and not is_data_issued:
        if client_response == "DATA":
            server_response = server_msg_dict[354]
            is_data_issued = True
        elif any(x in client_response for x in (' ', '\t')):
            server_response = server_msg_dict[501]
            is_data_issued = False
        else:
            server_response = server_msg_dict[500]
            is_data_issued = False
    else:
        if client_response == "DATA":
            server_response = server_msg_dict[354]
        elif any(x in client_response for x in (' ', '\t')):
            server_response = server_msg_dict[501]
        else:
            server_response = server_msg_dict[500]
        if server_response[:3] == "354":
            server_response = server_msg_dict[503]

    return [is_data_issued, server_response]


def tackle_noop_starting(client_response):
    if client_response == "NOOP":
        server_response = server_msg_dict[250]
    elif any(x in client_response for x in (' ', '\t')):
        server_response = server_msg_dict[501]
    else:
        server_response = server_msg_dict[500]

    return server_response


def prep_auth_starting(client_response):
    if client_response == "AUTH CRAM-MD5":
        chal_64base = base64.b64encode(
            secrets.token_bytes(32).decode(errors='ignore').encode('ascii', errors='ignore'))
        server_response = server_msg_dict[334]
    elif any(x in client_response for x in (' ', '\t')) or client_response.startswith("AUTH "):
        server_response = server_msg_dict[501]
        chal_64base = None
    else:
        server_response = server_msg_dict[500]
        chal_64base = None

    return [chal_64base, server_response]


def aux_auth_starting(client_response, chal_64base, is_authed, pid, loc_in_queue):
    if str(pid).isdigit() and str(loc_in_queue).isdigit():
        print(f"[{pid}][{loc_in_queue}]C: {client_response}\r\n", flush=True, end='')
    else:
        print(f"C: {client_response}\r\n", flush=True, end='')
    if client_response == "*":
        server_response = server_msg_dict[503]
    else:
        client_md5_digest = base64.b64decode(client_response).decode().split(" ")[1]
        server_md5_digest = \
            hmac.new(PERSONAL_SECRET.encode(), base64.b64decode(chal_64base), "md5").hexdigest()
        if client_md5_digest == server_md5_digest:
            server_response = server_msg_dict[235]
            is_authed = True
        else:
            server_response = server_msg_dict[535]

    return [server_response, is_authed]


def tackle_quit_starting(client_response):
    if client_response == "QUIT":
        server_response = server_msg_dict[221]
        is_port_working = False
    elif any(x in client_response for x in (' ', '\t')):
        server_response = server_msg_dict[501]
        is_port_working = True
    else:
        server_response = server_msg_dict[500]
        is_port_working = True

    return [is_port_working, server_response]


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

    if not os.access(utils.get_path(inbox_path), os.W_OK):
        sys.exit(2)
    if '' in (server_port, inbox_path):
        sys.exit(2)

    circuit_breaker(int(server_port), str(utils.get_path(inbox_path)))


def circuit_breaker(server_port, server_inbox_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('localhost', server_port))
    except:
        sys.exit(2)
    while True:
        sock.listen()
        connector_sock, address = sock.accept()
        connector(connector_sock, server_inbox_path)


def connector(sock, server_inbox_path, pid='', loc_in_queue=''):
    is_ehlo_issued = False
    is_mail_issued = False
    is_rcpt_issued = False
    is_data_issued = False

    is_port_working = True
    is_port_reset = False
    is_authed = False

    from_blank_cont = []
    to_blank_cont = []
    body_cont = []

    with sock:
        signal.signal(signal.SIGINT, lambda signum, frame: sigint_trigger(sock, pid, loc_in_queue))

        sock.sendall((server_msg_dict[220] + '\r\n').encode())
        if str(pid).isdigit() and str(loc_in_queue).isdigit():
            print(f"[{pid}][{loc_in_queue}]S: {server_msg_dict[220]}\r\n", flush=True, end='')
        else:
            print(f"S: {server_msg_dict[220]}\r\n", flush=True, end='')

        while is_port_working:
            raw_client_response = sock.recv(1024)

            if not raw_client_response:
                if str(pid).isdigit() and str(loc_in_queue).isdigit():
                    print(f"[{pid}][{loc_in_queue}]S: Connection lost\r\n", flush=True, end='')
                else:
                    print(f"S: Connection lost\r\n", flush=True, end='')
                return True

            client_response = raw_client_response.decode('utf-8', errors='ignore').strip('\r\n')

            if str(pid).isdigit() and str(loc_in_queue).isdigit():
                print(f"[{pid}][{loc_in_queue}]C: {client_response}\r\n", flush=True, end='')
            else:
                print(f"C: {client_response}\r\n", flush=True, end='')

            if is_ehlo_issued and is_mail_issued and is_rcpt_issued and is_data_issued:
                if client_response == '.':
                    server_response = server_msg_dict[250]
                    utils.txt_composer(from_blank_cont, to_blank_cont, body_cont, server_inbox_path, is_authed, pid,
                                     loc_in_queue)

                    is_ehlo_issued = True
                    is_mail_issued = False
                    is_rcpt_issued = False
                    is_data_issued = False
                    from_blank_cont = []
                    to_blank_cont = []
                    body_cont = []
                else:

                    server_response = server_msg_dict[354]
                    body_cont.append(client_response)
            elif client_response.startswith("RSET"):

                if client_response == "RSET":
                    server_response = server_msg_dict[250]
                    is_port_reset = True
                elif any(x in client_response for x in (' ', '\t')):
                    server_response = server_msg_dict[501]
                    is_port_reset = False
                else:
                    server_response = server_msg_dict[500]
                    is_port_reset = False

            elif client_response.startswith("EHLO"):

                if re.compile(utils.EHLO_FORMAT).match(client_response):
                    server_response = ["250", "127.0.0.1", "250 AUTH CRAM-MD5"]
                    is_port_reset = True
                elif any(x in client_response for x in (' ', '\t')) or client_response == "EHLO":
                    server_response = server_msg_dict[501]
                    is_port_reset = False
                else:
                    server_response = server_msg_dict[500]
                    is_port_reset = False
                if not (server_response in server_msg_dict.values()) and server_response[0] == "250":

                    is_ehlo_issued = True
                    is_mail_issued = False
                    is_rcpt_issued = False
                    is_data_issued = False
                    from_blank_cont = []
                    to_blank_cont = []
                    body_cont = []
                    is_port_reset = False

                    to_client = server_response[0] + " " + server_response[1] + f"\r\n{server_response[2]}"

                    sock.sendall((to_client + '\r\n').encode())
                    temp_msg = server_response[0] + " " + server_response[1]
                    if str(pid).isdigit() and str(loc_in_queue).isdigit():
                        print(f"[{pid}][{loc_in_queue}]S: {temp_msg}\r\n", flush=True, end='')
                        print(f"[{pid}][{loc_in_queue}]S: {server_response[2]}\r\n", flush=True, end='')
                    else:
                        print(f"S: {temp_msg}\r\n", flush=True, end='')
                        print(f"S: {server_response[2]}\r\n", flush=True, end='')
                    continue
            elif client_response.startswith("MAIL"):
                if is_ehlo_issued and not is_mail_issued and not is_rcpt_issued and not is_data_issued:
                    server_response, from_blank_cont, to_blank_cont, body_cont, is_mail_issued \
                        = tackle_mail_starting(from_blank_cont, to_blank_cont, body_cont, client_response)

                elif re.compile(utils.FROM_FORMAT).match(client_response) or client_response.startswith(("MAIL", "MAIL ")):
                    server_response = server_msg_dict[503]
                else:
                    server_response = server_msg_dict[500]
            elif client_response.startswith("RCPT"):
                if is_ehlo_issued and is_mail_issued and not is_data_issued:
                    is_rcpt_issued, to_blank_cont, server_response \
                        = tackle_rcpt_starting(is_rcpt_issued, to_blank_cont, client_response)

                elif re.compile(utils.RCPT_FORMAT).match(client_response) or client_response.startswith(("RCPT", "RCPT ")) or any(
                        x in client_response for x in (' ', '\t')):
                    server_response = server_msg_dict[503]
                else:
                    server_response = server_msg_dict[500]
            elif client_response.startswith("DATA"):
                is_data_issued, server_response = \
                    tackle_data_starting(is_ehlo_issued, is_mail_issued, is_rcpt_issued, is_data_issued, client_response)

            elif client_response.startswith("NOOP"):
                server_response = tackle_noop_starting(client_response)

            elif client_response.startswith("AUTH"):
                chal_64base, server_response = prep_auth_starting(client_response)

                if is_ehlo_issued and not is_mail_issued and not is_rcpt_issued and not is_data_issued:
                    if server_response[:3] == "334":
                        sock.sendall((server_response[:3] + " " + chal_64base.decode() + '\r\n').encode())

                        if str(pid).isdigit() and str(loc_in_queue).isdigit():
                            print(f"[{pid}][{loc_in_queue}]S: {server_response}\r\n", flush=True, end='')
                        else:
                            print(f"S: {server_response}\r\n", flush=True, end='')

                        client_response = sock.recv(1024).decode('utf-8', errors='ignore').strip('\r\n')

                        server_response, is_authed = \
                            aux_auth_starting(client_response, chal_64base, is_authed, pid, loc_in_queue)

                else:
                    if server_response[:3] == "334":
                        server_response = server_msg_dict[503]
            elif client_response.startswith("QUIT"):
                is_port_working, server_response = tackle_quit_starting(client_response)

                if server_response[:3] == "221":
                    sock.sendall((str(server_response) + '\r\n').encode())
                    if str(pid).isdigit() and str(loc_in_queue).isdigit():
                        print(f"[{pid}][{loc_in_queue}]S: {server_response}\r\n", flush=True, end='')
                    else:
                        print(f"S: {server_response}\r\n", flush=True, end='')
                    return True
            else:
                server_response = server_msg_dict[500]

            if is_port_reset:
                is_mail_issued = False
                is_rcpt_issued = False
                is_data_issued = False
                from_blank_cont = []
                to_blank_cont = []
                body_cont = []
                is_port_reset = False

            sock.sendall((str(server_response) + '\r\n').encode())

            if str(pid).isdigit() and str(loc_in_queue).isdigit():
                print(f"[{pid}][{loc_in_queue}]S: {server_response}\r\n", flush=True, end='')
            else:
                print(f"S: {server_response}\r\n", flush=True, end='')


if __name__ == '__main__':
    run()