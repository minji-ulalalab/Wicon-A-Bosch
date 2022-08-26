import threading
from constant import *
from common import *
from logger import logger


class DataProcess(threading.Thread):

    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        self.alive = True     

    def run(self):
        """
        basic start command : CONNECT_CONTROLLER, REQUEST VALUE
        *CONNECT_CONTROLLER is communication start with MID 0001.
        *TIGHTENING_SUBSCRIBE is Last tightening result data subscribe with MID 0002. It has to send after CONNECT_CONTROLLER.
        *SELECT_PSET(N) select parameter set with MID 0018.(N is PSET number to set).
        *TIGHTENING_ACK is ack message about 0061.

        This function receive a data from controller in real time.
        And the data can be classified by MID.
        """
        logger.debug("Communication start, send 0001 data to controller")
        send_data_to_controller(self.sock, CONNECT_CONTROLLER)
        while self.alive:
            try:
                controller_echo_data = self.sock.recv(1024)
                if controller_echo_data:
                    controller_echo_data = controller_echo_data.decode("utf-8")
                    logger.info("[Data rev] : " + controller_echo_data.strip())
                    mid_code = str(controller_echo_data[4:8].strip())
                    logger.info("[MID of Data] : " + mid_code)

                    if mid_code == "0002":
                        setting_data(mid_code, controller_echo_data)
                        send_data_to_controller(self.sock, TIGHTENING_SUBSCRIBE)
                        logger.debug("Request: Tightening subscribe")
                        send_data_to_controller(self.sock, SELECT_PSET1)
                        logger.debug("Request: Pset number change ")

                    elif mid_code == "0061":
                        setting_data(mid_code, controller_echo_data)
                        send_data_to_controller(self.sock, TIGHTENING_ACK)
                        send_data_to_controller(self.sock, BATTERY_LEVEL)
                        logger.debug("send tightening ack to keep connection with tool")

                    else:
                        pass
       
            except socket.timeout:
                pass

            except Exception as e:
                self.alive = False
                logger.error("socket error : " + str(e))

    

             

        

