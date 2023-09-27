# SMTP-CRAM_Server_Client_and_a_MitM_Attacker
 Python, Telnet, Netcat, SMTP-CRAM, Socket

## Digest

An email exchange applications that supports the SMTP-CRAM protocol in python. This includes a client, a server and an eavesdropper (middle-man attacker), which can apply MitM attack to the authentication mechanism. To demonstrate CRAM-MD5 indeed has its weakness, the eavesdropper is implemented such that a MitM attack can be performed.

- Implemented a client, a server, and a Man-in-the-Middle (MitM) which could handle multi-process messages.

- Deployed Simple Mail Transfer Protocol(SMTP) for all communications among the client/server/eavesdropper.

- Used Challenge-Response Authentication Mechanism (CRAM) along with MD5 Message-Digest Algorithm.

- Designed a MitM attacker can actively eavesdrop/intercept/forge communications between a server and client.

- Tested in Linux and Windows environment with Telnet and Netcat.



## Summary

On the high level, the program has the following functionalities:

All programs are capable of:

Log all socket transactions in a specific format and output to stdout.

The SMTP-CRAM server is capable of:

Prepare for any incoming client connection.
Receive emails from a client and save to disk.
Additionally, allow client authentication.
Allow multiple clients to connect simultaneously.
Termination upon receiving a SIGINT signal.

The SMTP-CRAM client is capable of:

Read mail messages on disk.
Send emails to the server.
Additionally, allow client authentication.
Termination after finishing sending all emails.

The SMTP-CRAM eavesdropper (middle-man attacker) can do active eavesdropping between a pair of given server (E.g.,the real server) and client (E.g.,the real client). It can intercept all socket messages passing between the real server and the real client without being discovered. You can think of the eavesdropper as a combination of one valid client and one valid server, in such way it can impersonate the real client without letting the real server to discover its eavesdropping. This means it is capable of:

Prepare for being connected to by the real client and connecting to the real server.
Capture the email sent by the real client and save to disk, without altering the content.
Additionally, comprise any client authentication.
Termination.
