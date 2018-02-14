import argparse
import socket
import sys
import threading
import time


def initiate():
    parser = argparse.ArgumentParser()
    parser.set_defaults()

    parser.add_argument('-t', '--target', action='store', help='address of target')
    parser.add_argument('-p', '--port', action='store', help='port to use')

    args = parser.parse_args()
    return args


def alert_new_connection(server_socket):
    while True:
        new_client_socket, new_address = server_socket.accept()
        new_client_socket.close()
        print("\n received a client socket from " + str(new_address) + ". please open a new window to handle")


def execute_shell_mode(client_socket):
    while True:
        try:
            message = input("shell#: ")
            message += "\n"
            byte_message = message.encode('utf-8')
            client_socket.send(byte_message)

            # wait for data back
            respond = get_client_respond(client_socket).decode('utf-8')
            print(respond)

        except BrokenPipeError:
            print("connection closed by client")
            break


def execute_upload_mode(client_socket):
    while True:
        try:
            directory = input("directory from which the file is uploaded: ")
            file_name = input("file name:  ")
            location = directory + file_name

            file_descriptor = open(location, "rb")  # write the file to current directory
            raw_contents = file_descriptor.read()
            file_descriptor.close()

            name_length = str(len(file_name))
            while len(name_length) < 3:  # support name length up to 999
                name_length = "0" + name_length
            message = (name_length + file_name).encode() + raw_contents
            client_socket.send(message)

            if get_client_respond(client_socket).decode('utf-8') == "OK":
                print("File uploaded")
            else:
                print("Failed to upload file")

        except FileNotFoundError:
            print("no such directory")
            continue

        except BrokenPipeError:
            print("connection closed by client")
            break


def execute_download_mode(client_socket):
    while True:
        try:
            directory = input("directory from which the file is downloaded: ")
            file_name = input("file name:  ")
            location = directory + file_name + "\n"
            byte_message = location.encode('utf-8')
            client_socket.send(byte_message)

            raw_contents = get_client_respond(client_socket)

            """
            skip if directory does not exist
            """
            try:
                if raw_contents.decode('utf-8') == "***":
                    print("Failed to download the file \nDirectory does not exist")
                    continue
            except UnicodeDecodeError:
                print("Not UTF-8 file")

            file_descriptor = open(file_name, "wb")  # write the file to current directory
            file_descriptor.write(raw_contents)
            file_descriptor.close()

            print("Download finished")

        except BrokenPipeError:
            print("connection closed by client")
            break


def get_client_respond(client_socket):
    """
    :param client_socket:
    :return: client respond in bytes
    """
    recv_len = 1
    respond = "".encode('utf-8')
    while recv_len > 0:
        data = client_socket.recv(4096)  # buffer size is 4096
        recv_len = len(data)
        respond += data

        if recv_len < 4096:
            break

    return respond


def server_listening(target, port):
    """
    TODO: alert user if received new connection requests
    """
    if not target:
        target = "0.0.0.0"  # all interfaces!!!!!!!!!!!!!!!!!

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)
    print("listening on " + target + ":" + str(port) + "......")

    client_socket, address = server.accept()
    print("received a client socket from " + str(address))

    threading.Thread(target=alert_new_connection, args=(server,)).start()  # alert if new request received
    # i.daemon = True

    first_respond = get_client_respond(client_socket).decode('utf-8')
    print(first_respond)

    if first_respond == "shell_mode":
        execute_shell_mode(client_socket)
    elif first_respond == "toserver_mode":
        execute_download_mode(client_socket)
    elif first_respond == "toclient_mode":
        execute_upload_mode(client_socket)
    else:
        print("wrong mode selected by the client")


def main():
    if not len(sys.argv[1:]):
        print("Black Hat Utility")
        print("use '-h' to print manual")
        return

    args = initiate()

    port = None
    target = None

    if args.target:
        target = args.target
    if args.port:
        port = int(args.port)

    if not port:
        print("missing port")
        return

    server_listening(target=target, port=port)


if __name__ == '__main__':
    main()
