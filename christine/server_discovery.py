"""This thread will handle the coordination and discovery of external servers and APIs that Christine will need to communicate with."""

import time
import socket
import threading

from christine import log

class Servers(threading.Thread):
    """Thread will listen to the UDP broadcast packets sent from servers on the local network."""

    name = "Servers"

    def __init__(self):
        super().__init__(daemon=True)

        self.wernicke_ip = None
        self.broca_ip = None
        self.llm_ip = None

    def run(self):

        # bind to the UDP ports
        wernicke_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wernicke_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        wernicke_sock.setblocking(False)
        wernicke_sock.bind(("0.0.0.0", 3000))
        broca_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broca_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broca_sock.setblocking(False)
        broca_sock.bind(("0.0.0.0", 3001))
        llm_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        llm_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        llm_sock.setblocking(False)
        llm_sock.bind(("0.0.0.0", 3002))

        # repeatedly listen for UDP packets, only when server not connected
        while True:

            time.sleep(15)

            try:

                if self.wernicke_ip is None:

                    log.server_discovery.debug('Checking for wernicke')
                    data, addr = wernicke_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.wernicke_ip = addr[0]
                        log.server_discovery.info('Received UDP packet from %s', self.wernicke_ip)

                if self.broca_ip is None:

                    log.server_discovery.debug('Checking for broca')
                    data, addr = broca_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.broca_ip = addr[0]
                        log.server_discovery.info('Received UDP packet from %s', self.broca_ip)

                if self.llm_ip is None:

                    log.server_discovery.debug('Checking for llm')
                    data, addr = llm_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.llm_ip = addr[0]
                        log.server_discovery.info('Received UDP packet from %s', self.llm_ip)

            except BlockingIOError:
                pass
                # log.server_discovery.error('Got a BlockingIOError')

servers = Servers()
