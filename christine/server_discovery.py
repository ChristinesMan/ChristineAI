"""This thread will listen for the broca and wernicke servers to broadcast their IP addresses. When the servers are found, the IP address is stored in the thread. This thread will run in the background and will only stop when the broca server is connected."""

import time
import socket
import threading

from christine import log

class ReceiveUDPLove(threading.Thread):
    """Thread will listen to the UDP broadcast packets sent from server."""

    name = "ReceiveUDPLove"

    def __init__(self):
        super().__init__(daemon=True)

        self.wernicke_ip = None
        self.broca_ip = None

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

        # repeatedly listen for UDP packets, only when server not connected
        while True:

            time.sleep(15)

            try:

                if self.wernicke_ip is None:

                    log.server_discovery.debug('Checking for wernicke')
                    data, addr = wernicke_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.wernicke_ip = addr[0]
                        log.server_discovery.debug('Received UDP packet from %s', self.wernicke_ip)

                if self.broca_ip is None:

                    log.server_discovery.debug('Checking for broca')
                    data, addr = broca_sock.recvfrom(1024)

                    if data == b'fuckme':
                        self.broca_ip = addr[0]
                        log.server_discovery.debug('Received UDP packet from %s', self.broca_ip)

            except BlockingIOError:
                log.server_discovery.error('Got a BlockingIOError')

servers = ReceiveUDPLove()
