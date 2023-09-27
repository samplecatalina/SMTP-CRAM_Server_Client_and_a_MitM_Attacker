from pathlib import Path
import time


INNER_DOMAIN_FORMULA = "(" + "[a-zA-Z0-9]+" + ")" + "(([a-zA-Z0-9]+|-)*[a-zA-Z0-9]+)?"
DOMAIN_FORMULA = "(" + INNER_DOMAIN_FORMULA + "(\.([a-zA-Z0-9]+)(([a-zA-Z0-9]+|-)*[a-zA-Z0-9]+)?)+" +")" + "|" + "\[((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}\]"
EMAIL_ADDR_FORMULA = "(" + "[a-zA-Z0-9]+" + "([a-zA-Z0-9]+|-)*" + ")" + "(\.[a-zA-Z0-9]+([a-zA-Z0-9]+|-)*)*" + "@" + DOMAIN_FORMULA

DATE_FORMAT = r'^(((Mon|Tue|Wed|Thu|Fri|Sat|Sun))[,]?\s[0-9]{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s([0-9]{4})\s([0-9]{2}):([0-9]{2})(:([0-9]{2}))?\s([\+|\-][0-9]{4})\s?$'
EMAIL_ADDR_FORMAT = rf'^(<({EMAIL_ADDR_FORMULA})>)$'

LOCALHOST = '127.0.0.1'
EHLO_FORMAT = r'^(EHLO)\s(((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4})$'
FROM_FORMAT = rf'^(MAIL FROM:)(<({EMAIL_ADDR_FORMULA})>)$'
RCPT_FORMAT = rf'^(RCPT TO:)(<({EMAIL_ADDR_FORMULA})>)$'



def get_path(path: str):
    if path[0:2] == '~/':
        path = path[2:]
    return Path.home() / Path(path)


def aux_txt_composer(body, is_authed, pid='', loc_in_queue=''):
    txt_file = ""
    subject = ""
    date = ""
    for line in body:
        if line.startswith("Date: "):
            date = line[6:]
            txt_file = str(int(time.mktime(time.strptime(date, "%a, %d %b %Y %H:%M:%S %z"))))
            body.remove(line)
    for line in body:
        if line.startswith("Subject: "):
            subject = line[9:]
            body.remove(line)
    if is_authed:
        txt_file = "auth." + txt_file
    if str(pid).isdigit() and str(loc_in_queue).isdigit():
        txt_file = f"[{pid}][{loc_in_queue}]" + txt_file

    return [date, subject, txt_file]


def txt_composer(from_blank_cont, to_blank_cont, body_cont, inbox, is_authed, pid='', loc_in_queue=''):

    date, subject, txt_file_to_write = aux_txt_composer(body_cont, is_authed, pid, loc_in_queue)
    txt_file_to_write = inbox + "/" + txt_file_to_write + ".txt"

    mail_to_write = open(txt_file_to_write, mode='w', encoding='utf-8')
    mail_to_write.write("From: " + from_blank_cont[0] + "\n" +
                        "To: " + ', '.join(to_blank_cont) + "\n" +
                        "Date: " + date + "\n" +
                        "Subject: " + subject + "\n")

    if body_cont:
        mail_to_write.write('\n'.join(body_cont))
        mail_to_write.write('\n')
    mail_to_write.close()