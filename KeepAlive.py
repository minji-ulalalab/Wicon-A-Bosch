import threading
from common import *
from constant import *


class KeepAlive(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        self.alive = True

    def run(self):
        """
        The integrator send a keep alive to the controller. The controller should only mirror and return the received keep alive to the integrator.
        if no message has been exchanged between the client and the controller for the last 15s,
        then the controller considers the connection lost and closes it.

        When time_check is True, send keep alive[9999] to controller.
        """
        logger.debug("Run the Keep alive thread for connection")
        while self.alive:
            try:
                if time_check():
                    self.send_keep_alive()
            except Exception as e:
                logger.error("keep alive run error : " + str(e))
                logger.debug("Close the Keep alive thread for connection")
                self.alive = False
                self.sock.close()

    def send_keep_alive(self):
        try:
            send_data_to_controller(self.sock, KEEP_ALIVE)
        except Exception as e:
            logger.error("keep alive sending error : " + str(e))

