from ServerResponse import ServerResponse

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

print(str(ServerResponse.s220))
print(ServerResponse.s220)

def print_server_stdout(str_to_print: str, pid='', order=''):
    if str(pid).isdigit() and str(order).isdigit():
        print(f"[{pid}][{order}]S: {str_to_print}\r\n", flush=True, end='')
    else:
        print(f"S: {str_to_print}\r\n", flush=True, end='')

print_server_stdout(ServerResponse.s220)
print(server_msg_dict[221])
print(server_msg_dict[220])
print(server_msg_dict[220][:3])
