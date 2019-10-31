import argparse
import socket
import sys
import threading

import paramiko


class Server(paramiko.ServerInterface):
    def __init__(self, username, password):
        self.event = threading.Event()
        self.username = username
        self.password = password

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if self.username == username and password == self.password:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED


def bind_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, port))
    return sock


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyfile', dest='keyfile', help='The key file for the server to use')
    parser.add_argument('-o', '--host', dest='host', help='IP to listen on')
    parser.add_argument('-p', '--port', dest='port', help='Port to listen on', type=int)
    # TODO: Key authentication
    parser.add_argument('-u', '--username', dest='username', help='Username to authenticate with')
    parser.add_argument('-a', '--password', dest='password', help='Password to authenticate with')
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    if args.keyfile == "":
        print('[!!] Keyfile not supplied')
        exit(1)
    try:
        sock = bind_socket(args.host, args.port)
        sock.listen(100)
    except Exception as e:
        print('[!!] Failed to bind socket')
        exit(1)
    try:
        (client, addr) = sock.accept()
    except Exception as e:
        print('[!!] Could not get a connection')
        exit(1)
    try:
        # Elevate our transport
        ssh_session = paramiko.Transport(client)
        key = paramiko.RSAKey.from_private_key_file(args.keyfile)
        ssh_session.add_server_key(key)
        server = Server(args.username, args.password)
        ssh_session.start_server(server=server)
        chan = ssh_session.accept(30)
    except Exception as e:
        print('[!!] Could not elevate our socket to SSH transport')
        print(e)
        exit(1)
    print("[+] *90s hacker voice* I'm in")
    chan.send(b'Welcome to cool_and_totally_not_sarcastic_hacker_ssh')
    try:
        while True:
            try:
                command = input('Enter command: ').strip('\n')
                if command == 'exit':
                    chan.send(b'exit')
                    break
                chan.send(command.encode())
                print(chan.recv(1024).decode('utf-8'))
            except KeyboardInterrupt:
                print('[!!] Caught a keyboard interrupt')
                break
            except Exception as e:
                print('[!!] Caught an exception: ' + str(e))
                break
    finally:
        ssh_session.close()