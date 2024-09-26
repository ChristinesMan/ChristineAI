"""This thread will handle the coordination and discovery of external servers and APIs that Christine will need to communicate with."""

import time
import socket
import threading

from christine import log
from christine.config import CONFIG

class Servers(threading.Thread):
    """Thread will listen to the UDP broadcast packets sent from servers on the local network."""

    name = "Servers"

    def __init__(self):
        super().__init__(daemon=True)

        # check the config for the server IPs and save whether they are enabled or not
        self.wernicke_enabled = CONFIG['wernicke'].getboolean('enabled')
        self.broca_enabled = CONFIG['broca'].getboolean('enabled')

        # initialize the server IPs to None if they set to auto, or disabled
        if CONFIG['wernicke']['server'] == 'auto' or not self.wernicke_enabled:
            self.wernicke_ip = None
        else:
            self.wernicke_ip = CONFIG['wernicke']['server']

        if CONFIG['broca']['server'] == 'auto' or not self.broca_enabled:
            self.broca_ip = None
        else:
            self.broca_ip = CONFIG['broca']['server']

    def run(self):

        # log the initial state of the servers
        log.server_discovery.info('Wernicke enabled: %s', self.wernicke_enabled)
        log.server_discovery.info('Broca enabled: %s', self.broca_enabled)
        log.server_discovery.info('Wernicke IP: %s', self.wernicke_ip)
        log.server_discovery.info('Broca IP: %s', self.broca_ip)

        # bind to the UDP ports (if enabled)
        if self.wernicke_enabled:
            wernicke_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            wernicke_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            wernicke_sock.setblocking(False)
            wernicke_sock.bind(("0.0.0.0", 3000))
        if self.broca_enabled:
            broca_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broca_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broca_sock.setblocking(False)
            broca_sock.bind(("0.0.0.0", 3001))

        # repeatedly listen for UDP packets, only when server not connected and enabled
        while True:

            time.sleep(15)

            try:

                if self.wernicke_enabled and self.wernicke_ip is None:

                    log.server_discovery.debug('Checking for wernicke')
                    data, addr = wernicke_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.wernicke_ip = addr[0]
                        log.server_discovery.info('Received UDP packet from %s', self.wernicke_ip)

                if self.broca_enabled and self.broca_ip is None:

                    log.server_discovery.debug('Checking for broca')
                    data, addr = broca_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.broca_ip = addr[0]
                        log.server_discovery.info('Received UDP packet from %s', self.broca_ip)

            except BlockingIOError:
                pass
                # log.server_discovery.error('Got a BlockingIOError')

servers = Servers()
