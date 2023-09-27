def get_sender_det(raw):
    """
    get sender's detail
    :param raw: the line with
    :return: a list contains sender's details in string format
    """
    if raw.startswith("From: "):
        if EMAIL_ABNF_REGEX.search(raw[6:]) is not None:
            return [EMAIL_ABNF_REGEX.search(raw[6:]).group()]
    return None  # TODO check if this return None is actually needed


def get_receiver_det(raw):
    """
    get receiver's detail
    :param raw: the line with
    :return: a list containing receiver's detail in string format
    """
    if raw.startswith("To: "):
        list_of_email = raw[4:].split(',')
        if len(list_of_email) <= 0:
            # return None
            return
        # recver_det = [EMAIL_ABNF_REGEX.search(email).group() for email in list_of_email]
        recver_det = []
        for e in list_of_email:
            recver_det.append(EMAIL_ABNF_REGEX.search(e).group())

        if None in recver_det:
            # return None
            return

        return recver_det
    # return None


def get_subject(raw):
    """
    get the subject of an email
    :param raw: the line with
    :return: a string of an email subject
    """
    if raw.startswith("Subject: "):
        return raw[9:]
    # return None


def get_date(raw):
    """
    get the date of an email
    :param raw: the line with
    :return: a string of an email's date
    """
    if raw.startswith("Date: "):
        if DATE_RFC5322_REGEX.search(raw[6:]) is not None:
            return DATE_RFC5322_REGEX.search(raw[6:]).group()
    # return None


def email_assembler(send_path, mail_to_send):
    """
    screen the raw email content in config format and pick out all email elements
    :param send_path: directory in which holds all emails to be sent
    :param mail_to_send: every raw email in config format
    :return: bool is_auth, list sender_det, list receiver_det, str date, str subject, str mail_content
    """
    is_auth = False
    if mail_to_send.startswith("auth-"):
        is_auth = True

    # read in elements of a formatted email
    sender_det = []
    receiver_det = []
    date = ""
    subject = ""
    mail_content = []

    mail_raw = open(send_path + Path(mail_to_send), mode='r')
    mail_raw_params = mail_raw.readlines()
    i = 0
    while i < len(mail_raw_params):
        raw_line = mail_raw_params[i].strip("\n")
        if i == 0:  # get sender details
            if raw_line.startswith("From: "):
                if EMAIL_ABNF_REGEX.search(raw_line[6:]) is not None:
                    sender_det = [EMAIL_ABNF_REGEX.search(raw_line[6:]).group()]
            else:
                sender_det = None
            # sender_det = get_sender_det(raw_line)
        elif i == 1:
            receiver_det = get_receiver_det(raw_line)
        elif i == 2:
            if raw_line.startswith("Date: "):
                if DATE_RFC5322_REGEX.search(raw_line[6:]) is not None:
                    date = DATE_RFC5322_REGEX.search(raw_line[6:]).group()
            else:
                date = None
            # date = get_date(raw_line)
        elif i == 3:
            if raw_line.startswith("Subject: "):
                subject = raw_line[9:]
            else:
                subject = None
            # subject = get_subject(raw_line)
        else:
            mail_content.append(raw_line)
        i += 1
    mail_raw.close()

    return is_auth, sender_det, receiver_det, date, subject, mail_content

def send(is_auth: int, sender_det: list[str], receiver_det: list[str], date: str, subject: str, mail_content: list[str], client_server_port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('localhost', client_server_port))
        except socket.error:
            print_client_stdout("Cannot establish connection")
            sys.exit(3)

        while True:
            server_response = s.recv(1024)
            raw_server_response = smtp_decode(server_response)

            if raw_server_response.endswith("250 AUTH CRAM-MD5"):
                raw_server_response = raw_server_response.split("\r\n")
                print_server_stdout(raw_server_response[0])
                print_server_stdout(raw_server_response[1])
                smtp_code, smtp_parameter = response_server_parse(raw_server_response[0])
            else:
                print_server_stdout(raw_server_response)
                smtp_code, smtp_parameter = response_server_parse(raw_server_response)

            if smtp_code == "220":
                s.sendall(smtp_encode(f"EHLO {LOCALHOST}"))
                print_client_stdout(f"EHLO {LOCALHOST}")
            elif smtp_code == "250":
                if is_auth:
                    s.sendall(smtp_encode("AUTH CRAM-MD5"))
                    print_client_stdout("AUTH CRAM-MD5")
                elif smtp_parameter == LOCALHOST:
                    source_buffer = "MAIL FROM:" + sender_det[0]
                    s.sendall(smtp_encode(source_buffer))
                    print_client_stdout(source_buffer)
                elif smtp_parameter == "Requested mail action okay completed":
                    if len(receiver_det) != 0:
                        destination_buffer = "RCPT TO:" + receiver_det[0]
                        s.sendall(smtp_encode(destination_buffer))
                        print_client_stdout(destination_buffer)
                        receiver_det.remove(receiver_det[0])
                    elif len(receiver_det) == 0 and len(mail_content) == 0 and len(date) == 0 and len(subject) == 0:
                        s.sendall(smtp_encode("QUIT"))
                        print_client_stdout("QUIT")
                        smtp_code, smtp_parameter = response_server_parse(smtp_decode(s.recv(1024)))
                        print_server_stdout(construct_message(smtp_code, smtp_parameter))
                        return
                    elif len(receiver_det) == 0:
                        s.sendall(smtp_encode("DATA"))
                        print_client_stdout("DATA")
            elif smtp_code == "235":
                source_buffer = "MAIL FROM:" + sender_det[0]
                s.sendall(smtp_encode(source_buffer))
                print_client_stdout(source_buffer)
            elif smtp_code == "334":
                md5digest_client = PERSONAL_ID + " " + md5digest_client + hmac.new(PERSONAL_SECRET.encode(), base64.b64decode(smtp_parameter), 'md5').hexdigest()
                s.sendall(smtp_encode(md5digest_client.encode()))
                print_client_stdout(md5digest_client)
            elif smtp_code == "354":
                if date != '':
                    s.sendall(smtp_encode("Date: " + date))
                    print_client_stdout("Date: " + date)
                    date = ''
                elif subject != '':
                    s.sendall(smtp_encode("Subject: " + subject))
                    print_client_stdout("Subject: " + subject)
                    subject = ''
                elif len(mail_content) != 0:
                    s.sendall(smtp_encode(mail_content[0]))
                    print_client_stdout(mail_content[0])
                    mail_content.remove(mail_content[0])
                elif len(mail_content) == 0:
                    s.sendall(smtp_encode("."))
                    print_client_stdout(".")