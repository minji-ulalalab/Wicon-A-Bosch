from DataProcess import DataProcess
from KeepAlive import *
from common import *
from logger import logger


all_threads = []


def main():
    logger.info("start the Wicon-A")
    """
    Two threads are running.
    [thread1]data_process is for getting data from controller in real time.
    [thread2]keep_alive is for sending data to controller to check communication.
    """
    try:
        sock = socket_connect()

        data_process = DataProcess(sock)
        data_process.start()
        all_threads.append(data_process)

        keep_alive = KeepAlive(sock)
        keep_alive.start()
        all_threads.append(keep_alive)

        for thread in all_threads:
            thread.join()

    except Exception as e:
        logger.error("main error : " + str(e))


if __name__ == "__main__":
    main()
