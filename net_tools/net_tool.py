import argparse
import socket
import subprocess
import threading


def initiate():
    parser = argparse.ArgumentParser(description="some message")
    parser.set_defaults(intro="Black Hat Utility")

    parser.add_argument('-t', '--target', action='store', help='address of target')
    parser.add_argument('-p', '--port', action='store', help='port to use')
    parser.add_argument('-l', '--listen', action='store', choices=['Y', 'N'],
                        help='listen on [host]:[port] for incoming connection (Y/N)')
    parser.add_argument('-e', '--execute', action='store', help='execute the given file upon receiving a command shell')
    parser.add_argument('-c', '--command', action='store', help='initialize a command shell')
    parser.add_argument('-u', '--upload', action='store',
                        help='upon receiving connection upload a file and writh to [destination]')
    args = parser.parse_args()
    # print(args)
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
                respond += data

                if recv_len < 4096:  # this condition looks suspicious!!!!!!!!!!!!!!!!!!!
                    break

            print(respond.decode('utf-8'))
            print("finish sending")


def run_command(command):
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


def client_handler(client_socket, upload_destination, execute, command):
    """
    TODO: finish up 'upload'
    """
    if not upload_destination and not execute and not command:
        client_socket.send("?".encode('utf-8'))

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

    if execute:
        output = run_command(execute)
        client_socket.send(output)

    if command:
        while True:
            client_socket.send("<BHP:#> ")
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            respond = run_command(cmd_buffer)

            client_socket.send(respond)


def server_loop(target, port, upload, execute, command):
    if not target:
        target = "0.0.0.0"  # all interfaces!!!!!!!!!!!!!!!!!

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))  # bind the socket to a public host and a well-known port
    server.listen(5)  # don't understand this
    print("listening......")
    while True:
        client_socket, address = server.accept()
        print("receive a client socket from " + str(address))
        # create a thread whenever a client connects to the server
        client_thread = threading.Thread(target=client_handler, args=(client_socket, upload, execute, command))
        client_thread.start()


def main():
    args = initiate()

    listen = None
    port = None
    execute = None
    command = None
    upload_location = None
    target = None

    if args.listen == "Y":
        listen = True
    if args.target:
        target = args.target
    if args.port:
        port = int(args.port)
    if args.execute:
        execute = args.execute
    if args.command:
        command = args.command
    if args.upload:
        upload_location = args.upload

    if not listen:  # client
        if not port or not target:
            print("client mode" + "\n" + "missing port or target address")
        else:
            # buffer = sys.stdin.read()  # read from terminal and send to the server; stop when ctrl + D
            client_sender(target, port)

    if listen:  # server
        if not port:
            print("server mode" + "\n" + "missing port")
        else:
            server_loop(target, port, upload_location, execute, command)


if __name__ == '__main__':
    main()
