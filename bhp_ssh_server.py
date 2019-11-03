import argparse
import select
import socket
import sys
import threading

import paramiko


class SshServer(paramiko.ServerInterface):
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

    def get_banner(self):
        return 'Welcome to the super happy fun time jamboree!', 'en-US'


class Server:
    def __init__(self, ip, port, ssh_server, key):
        self.ip = ip
        self.port = port
        self.sockets = []
        self.address_lookup = dict()
        self.ssh_server = ssh_server
        self.stop = False
        self.key = key
        self.reader_thread = threading.Thread(target=self.__listen_loop)
        self.accept_thread = threading.Thread(target=self.__accept_loop)

    def __read_msgs(self, socks):
        buffers = dict()
        # Initialise the buffers
        for sock in socks:
            buffers[sock] = bytearray()
        to_read = socks
        while len(to_read) > 0:
            # Loop over and build up our buffers
            (to_read, _, _) = select.select(to_read, [], [], 0.001)
            non_zero = []
            for sock in to_read:
                msg = sock.recv(1024)

                if len(msg) == 0 or msg == b'\xff\xf4\xff\xfd\x06':
                    buffers[sock] = b''
                    continue
                buffers[sock].extend(msg)
                non_zero.append(sock)
            to_read = non_zero
        return buffers

    def __listen_loop(self):
        try:
            while not self.stop:
                (reads, _, _) = select.select(self.sockets, [], [], 1)
                if len(reads) == 0:
                    continue
                buffs = self.__read_msgs(reads)
                for k in buffs.keys():
                    v = buffs[k]
                    if len(v) == 0:
                        self.sockets.remove(k)
                        self.address_lookup.pop(k)
                        print('[*] Socket shutdown')
                        continue
                    print('[<] Received "{}" from {}'.format(v.decode('utf-8').strip(), self.address_lookup[k]))
        except KeyboardInterrupt as e:
            print('[!!] Caught a keyboard interrupt, shutting it down')
            self.stop = True
        finally:
            for sock in self.sockets:
                sock.close()

    def __accept_loop(self):
        self.server_sock.listen(100)
        while not self.stop:
            try:
                (client, addr) = self.server_sock.accept()
                if self.stop:
                    continue
                print("[<] Received connection from {}".format(addr))
                # Elevate our socket to an SSH socket
                ssh_session = paramiko.Transport(client)
                ssh_session.add_server_key(self.key)
                ssh_session.start_server(server=self.ssh_server)
                chan = ssh_session.accept(30)
                print("[+] Connection from {} elevated".format(addr))
                chan.send(b'Welcome to cool_and_totally_not_sarcastic_hacker_ssh')
                self.sockets.append(chan)
                self.address_lookup[chan] = addr
            except KeyboardInterrupt as e:
                self.stop = True
                print('[!!] Caught keyboard interrupt, shutting down')
            except InterruptedError as e:
                self.stop = True
                print('[!!] Interupted, extiting')
            except Exception as e:
                print('[!!] Problem creating connection')

    def __input_loop(self):
        try:
            while not self.stop:
                cmd = input("Enter command: ")
                if cmd == 'exit':
                    break
                for s in self.sockets:
                    s.send(cmd.encode())
        except KeyboardInterrupt as e:
            print('')
            print("[!!] Caught keyboard interrupt, exiting")
        self.stop = True
        # Force the listen loop to quit
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.ip, self.port))
        self.accept_thread.join()
        self.reader_thread.join()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.ip, self.port))
        self.server_sock = sock
        self.accept_thread.start()
        self.reader_thread.start()
        self.__input_loop()


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyfile', dest='keyfile', help='The key file for the server to use')
    parser.add_argument('-o', '--host', dest='host', help='IP to listen on')
    parser.add_argument('-p', '--port', dest='port', help='Port to listen on', type=int)
    parser.add_argument('-l', '--key-length', dest='keylength', default=2048,
                        help='Length of the key to generate', type=int)
    # TODO: Key authentication
    parser.add_argument('-u', '--username', dest='username', help='Username to authenticate with')
    parser.add_argument('-a', '--password', dest='password', help='Password to authenticate with')
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    if args.keyfile:
        key = paramiko.RSAKey.from_private_key_file(args.keyfile)
    else:
        key = paramiko.RSAKey.generate(args.keylength)
    ssh_server = SshServer(args.username, args.password)
    server = Server(args.host, args.port, ssh_server, key)
    server.run()
