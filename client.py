import re
from pathlib import Path

import os
import socket
import sys
import hmac
import base64

import utils

PERSONAL_ID = "764BFC"
PERSONAL_SECRET = "a69e820263d9dcfd4aceebb02bcd5f71"


def get_receiver_det(raw):
    """
    get receiver's detail
    :param raw: the line with
    :return: a list containing receiver's detail in string format
    """
    recver_det = []
    if raw.startswith("To: "):
        list_of_email = raw[4:].split(',')
        if not list_of_email:
            return None
        for e in list_of_email:
            recver_det.append(re.compile(utils.EMAIL_ADDR_FORMAT).search(e).group())
        if None in recver_det:
            return None
        return recver_det
    return None


def send(send_path, mail_to_send, client_server_port: int):
    """
    assemble the emails by the config, then send out emails via socket
    :param send_path: directory in which holds all emails to be sent
    :param mail_to_send: every raw email in config format
    :param client_server_port: designated server port of client
    :return: None
    """
    is_auth = False
    if mail_to_send.startswith("auth-"):
        is_auth = True

    sender_det = []
    receiver_det = []
    date = ""
    subject = ""
    mail_content = []

    mail_raw = open(send_path / Path(mail_to_send), mode='r')
    mail_raw_params = mail_raw.readlines()
    i = 0
    while i < len(mail_raw_params):
        raw_line = mail_raw_params[i].strip("\n")
        if i == 0:
            if raw_line.startswith("From: "):
                if re.compile(utils.EMAIL_ADDR_FORMAT).search(raw_line[6:]) is not None:
                    sender_det = [re.compile(utils.EMAIL_ADDR_FORMAT).search(raw_line[6:]).group()]
            else:
                sender_det = None
        elif i == 1:
            receiver_det = get_receiver_det(raw_line)
        elif i == 2:
            if raw_line.startswith("Date: "):
                if re.compile(utils.DATE_FORMAT).search(raw_line[6:]) is not None:
                    date = re.compile(utils.DATE_FORMAT).search(raw_line[6:]).group()
            else:
                date = None
        elif i == 3:
            if raw_line.startswith("Subject: "):
                subject = raw_line[9:]
            else:
                subject = None
        else:
            mail_content.append(raw_line)
        i += 1
    mail_raw.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', client_server_port))
    except:
        print(f"C: Cannot establish connection\r\n", end='')
        sys.exit(3)
    while True:
        server_response = sock.recv(1024)
        raw_server_response = server_response.decode("utf-8", "ignore").strip('\r\n')
        if raw_server_response.endswith("250 AUTH CRAM-MD5"):
            raw_server_response = raw_server_response.split("\r\n")
            print(f"S: {raw_server_response[0]}\r\n", end='')
            print(f"S: {raw_server_response[1]}\r\n", end='')
            smtp_code = raw_server_response[0][0:3]
            smtp_parameter = raw_server_response[0][4:]
        else:
            print(f"S: {raw_server_response}\r\n", end='')
            smtp_code = raw_server_response[0:3]
            smtp_parameter = raw_server_response[4:]
        if smtp_code == "220":
            sock.sendall((f"EHLO {utils.LOCALHOST}" + '\r\n').encode())
            print(f"C: EHLO {utils.LOCALHOST}\r\n", end='')
        elif smtp_code == "250":
            if is_auth:
                sock.sendall(("AUTH CRAM-MD5" + '\r\n').encode())
                print(f"C: AUTH CRAM-MD5\r\n", end='')
            elif smtp_parameter == utils.LOCALHOST:
                source_buffer = "MAIL FROM:" + sender_det[0]
                sock.sendall((source_buffer + '\r\n').encode())
                print(f"C: {source_buffer}\r\n", end='')
            elif smtp_parameter == "Requested mail action okay completed":
                if len(receiver_det) != 0:
                    destination_buffer = "RCPT TO:" + receiver_det[0]
                    sock.sendall((destination_buffer + '\r\n').encode())
                    print(f"C: {destination_buffer}\r\n", end='')
                    receiver_det.pop(0)
                elif not receiver_det and not mail_content and not date and not subject:
                    sock.sendall(("QUIT" + '\r\n').encode())
                    print(f"C: QUIT\r\n", end='')
                    recv_msg = sock.recv(1024)
                    smtp_code = recv_msg.decode('utf-8', 'ignore').strip('\r\n')[0:3]
                    smtp_parameter = recv_msg.decode('utf-8', 'ignore').strip('\r\n')[4:]
                    wrapped_msg = smtp_code + " " + smtp_parameter
                    print(f"S: {wrapped_msg}\r\n", file=sys.stdout, end='')
                    return
                elif len(receiver_det) == 0:
                    sock.sendall(("DATA" + '\r\n').encode())
                    print(f"C: DATA\r\n", end='')
        elif smtp_code == "235":
            source_buffer = "MAIL FROM:" + sender_det[0]
            sock.sendall(({source_buffer} + '\r\n').encode())
            print(f"C: {source_buffer}\r\n", end='')
        elif smtp_code == "334":
            md5digest_client = PERSONAL_ID + " " + md5digest_client + \
                               hmac.new(PERSONAL_SECRET.encode(), base64.b64decode(smtp_parameter),
                                        'md5').hexdigest()
            encoded_md5digest_client = md5digest_client.encode()
            sock.sendall((encoded_md5digest_client + '\r\n').encode())
            print(f"C: {md5digest_client}\r\n", end='')
        elif smtp_code == "354":
            if date != '':
                sock.sendall(("Date: " + date + '\r\n').encode())
                print(f"C: Date: {date}\r\n", end='')
                date = ''
            elif subject != '':
                subject_cont = "Subject: " + subject
                sock.sendall((subject_cont + '\r\n').encode())
                print(f"C: {subject_cont}\r\n", end='')
                subject = ''
            elif len(mail_content) != 0:
                sock.sendall((mail_content[0] + '\r\n').encode())
                print(f"C: {mail_content[0]}\r\n", end='')
                mail_content.remove(mail_content[0])
            elif len(mail_content) == 0:
                sock.sendall(("." + '\r\n').encode())
                print(f"C: .\r\n", end='')


def run():
    if len(sys.argv) < 2:
        sys.exit(1)

    server_port = ''
    send_path = ''

    with open(sys.argv[1], mode='r', encoding='utf-8') as f:
        for line in f:
            line = line.strip('\n').split('=')
            if line[0] == "server_port":
                server_port = line[1]
            elif line[0] == "send_path":
                send_path = line[1]
    if not os.access(utils.get_path(send_path), os.R_OK):
        sys.exit(2)
    if '' in (server_port, send_path):
        sys.exit(2)

    server_port = int(server_port)
    send_path = str(utils.get_path(send_path))

    mailbox = []
    for i in os.listdir(send_path):
        if os.path.isfile(os.path.join(send_path, i)):
            mailbox.append(i)

    for mail in sorted(mailbox):

        sender_det = []
        receiver_det = []
        date = ""
        subject = ""
        mail_content = []

        mail_raw = open(send_path / Path(mail), mode='r')
        mail_raw_params = mail_raw.readlines()
        i = 0
        while i < len(mail_raw_params):
            raw_line = mail_raw_params[i].strip("\n")
            if i == 0:
                if raw_line.startswith("From: "):
                    if re.compile(utils.EMAIL_ADDR_FORMAT).search(raw_line[6:]) is not None:
                        sender_det = [re.compile(utils.EMAIL_ADDR_FORMAT).search(raw_line[6:]).group()]
                else:
                    sender_det = None
            elif i == 1:
                receiver_det = get_receiver_det(raw_line)
            elif i == 2:
                if raw_line.startswith("Date: "):
                    if re.compile(utils.DATE_FORMAT).search(raw_line[6:]) is not None:
                        date = re.compile(utils.DATE_FORMAT).search(raw_line[6:]).group()
                else:
                    date = None
            elif i == 3:
                if raw_line.startswith("Subject: "):
                    subject = raw_line[9:]
                else:
                    subject = None
            else:
                mail_content.append(raw_line)
            i += 1
        mail_raw.close()

        if None in (sender_det, receiver_det, date, subject, mail_content):
            print(f"C: {send_path}/{mail}: Bad formation\r\n", end='')
            continue
        send(send_path, mail, server_port)


if __name__ == '__main__':
    run()