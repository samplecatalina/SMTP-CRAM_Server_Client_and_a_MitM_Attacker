# SMTP-CRAM_Server_Client_and_a_MitM_Attacker
*Python, Telnet, Netcat, SMTP-CRAM, Socket*

Completed in Nov. 2022

## Digest

This project is an implementation of an SMTP-CRAM (Simple Mail Transfer Protocol - Challenge Response Authentication Mechanism) Server and Client, along with a Man-in-the-Middle (MitM) Attacker. It demonstrates an understanding of network protocols, security mechanisms, and advanced Python programming, showcasing the ability to develop, analyze, and secure network communications.

- Implemented a client, a server, and a Man-in-the-Middle (MitM) which could handle multi-process messages.

- Deployed Simple Mail Transfer Protocol(SMTP) for all communications among the client/server/eavesdropper.

- Used Challenge-Response Authentication Mechanism (CRAM) along with MD5 Message-Digest Algorithm.

- Designed a MitM attacker that can actively eavesdrop/intercept/forge communications between a server and a client.

- Tested in Linux and Windows environments with Telnet and Netcat.

## Features

- SMTP-CRAM Server and Client: Implements the SMTP protocol with CRAM to securely authenticate users and transfer emails.
- MitM Attacker: Simulates a Man-in-the-Middle attacker capable of eavesdropping and potentially altering communications between the server and client.
- Multiprocessing: Efficiently handles multiple processes to manage concurrent connections and ensure smooth and responsive interactions.
- Robust Error Handling: Implements comprehensive error handling to manage unexpected situations and maintain stability.
- Modular Design: The codebase is organized into modular components, promoting maintainability, scalability, and readability.

## Technical Stack
- Programming Language: Python
- Networking: Socket Programming
- Security: CRAM (Challenge Response Authentication Mechanism)
- Concurrency: Multiprocessing

## Code Structure
- server.py: Implements the SMTP-CRAM server logic.
- client.py: Implements the SMTP-CRAM client logic.
- eavesdropper.py: Implements the MitM attacker logic.
- multiprocess_server.py: Manages multiprocessing for handling concurrent connections.
- ServerResponse.py: Defines server responses.
- utils.py: Contains utility functions and helpers.

## Overview

On the high level, the program has the following functionalities:

All programs are capable of:

- Log all socket transactions in a specific format and output to stdout.

The SMTP-CRAM server is capable of:

- Prepare for any incoming client connection.
- Receive emails from a client and save them to disk.
- Additionally, allow client authentication.
- Allow multiple clients to connect simultaneously.
- Termination upon receiving a SIGINT signal.

The SMTP-CRAM client is capable of:

- Read mail messages on disk.
- Send emails to the server.
- Additionally, allow client authentication.
- Termination after finishing sending all emails.

The SMTP-CRAM eavesdropper (middle-man attacker):
can do active eavesdropping between a pair of given servers (E.g. the real server) and a client (E.g. the real client). 
It can intercept all socket messages passing between the real server and the real client without being discovered. You can think of the eavesdropper as a combination of one valid client and one valid server, in such a way it can impersonate the real client without letting the real server discover its eavesdropping. 

This means it is capable of:
- Prepare for being connected to the real client and connecting to the real server.
- Capture the email sent by the real client and save it to disk, without altering the content.
- Additionally, comprise any client authentication.
- Termination.
