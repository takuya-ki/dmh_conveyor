#!/usr/bin/env python3

import socket
import argparse

from belcon_mini_III import DMH

COMMAND_HELP = """
-----
Available commands

nl: normal rotation with low speed
nm: normal rotation with middle speed
nh: normal rotation with high speed
rl: reverse rotation with low speed
rm: reverse rotation with middle speed
rh: reverse rotation with high speed
nXX (rYY): drive with a set of rotation and speed [Hz/100] values
stop: stop the motion
complete: finish program
-->"""

# Map shorthand command keys to (direction, speed) tuples
MOVE_COMMANDS = {
    'nl': ('normal',  'low'),
    'nm': ('normal',  'middle'),
    'nh': ('normal',  'high'),
    'rl': ('reverse', 'low'),
    'rm': ('reverse', 'middle'),
    'rh': ('reverse', 'high'),
}


def commands(usbport, command_mode, ip, sockport):
    """Accepts commands locally or via socket and drives the conveyor."""
    dmh = DMH(usbport)
    dmh.get_set_mode()

    clientsock = None
    completemsg = 'complete'.encode('utf-8')

    if command_mode == 'external':
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind((ip, sockport))
        serversock.listen(10)
        serversock.settimeout(300)
        print('Waiting for connections...')
        clientsock, client_address = serversock.accept()
        serversock.close()  # no longer needed after accept
        clientsock.settimeout(3600)

    def send_complete():
        if command_mode == 'external' and clientsock is not None:
            clientsock.sendall(completemsg)

    try:
        while True:
            if command_mode == 'local':
                key = input(COMMAND_HELP)
            else:
                raw = clientsock.recv(1024)
                if not raw:  # connection closed by peer
                    print("Client disconnected.")
                    break
                key = raw.decode('utf-8')

            if key == 'complete':
                print("Finished.")
                dmh.stop()
                send_complete()
                break

            elif key == 'stop':
                print("Just stopped.")
                dmh.stop()
                send_complete()

            elif key in MOVE_COMMANDS:
                direction, speed = MOVE_COMMANDS[key]
                print("%s with %s speed." % (direction.capitalize(), speed))
                dmh.move(direction, speed)
                send_complete()

            elif len(key) >= 2 and key[0] in ('n', 'r'):
                direction = 'normal' if key[0] == 'n' else 'reverse'
                try:
                    dmh.move(direction, key[1:])
                    send_complete()
                except ValueError:
                    pass

            dmh.sleep_with_displaying_freq(0.1)

    finally:
        if clientsock is not None:
            clientsock.close()
        dmh.close_connection()


def get_options():
    """Returns user-specific options."""
    parser = argparse.ArgumentParser(
        description='Set options.')
    parser.add_argument(
        '--usbport', dest='usbport',
        type=str, default=None,
        help='set usb port number for the DINV U4 cable')
    parser.add_argument(
        '--command_from', dest='command_from',
        type=str, default='local',
        choices=['local', 'external'],
        help='set mode, [local] or [external]')
    parser.add_argument(
        '--ip', dest='ip',
        type=str, default="169.0.0.1",
        help='set ip address set for the local machine')
    parser.add_argument(
        '--sockport', dest='sockport',
        type=int, default=50007,
        help='set port number for the socket connection')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_options()
    commands(
        args.usbport,
        args.command_from,
        args.ip,
        args.sockport)
