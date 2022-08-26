import os
import logging.handlers

current_dir = os.path.dirname(os.path.realpath(__file__))  # [D:\스마트체결솔루션\test_openprotocol\scr\common]
current_file = os.path.basename(__file__)  # [logger.py]
current_file_name = current_file[:-3]  # [logger]

log_dir = '{}/logs'.format(current_dir)  # [D:\스마트체결솔루션\test_openprotocol\scr\common]
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

LOG_FILENAME = log_dir + '/' + '{}'.format(current_file_name)

logger = logging.getLogger('master')
logger.setLevel(logging.DEBUG)  # logging level: DEBUG


file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=LOG_FILENAME, when='midnight', interval=1, encoding='utf-8'
)
file_handler.suffix = 'log-%Y%m%d'

logger.addHandler(file_handler)
formatter = logging.Formatter(
    '[%(asctime)s][%(levelname)s] %(message)s'
)

file_handler.setFormatter(formatter)

streamHander = logging.StreamHandler()
streamHander.setFormatter(formatter)
logger.addHandler(streamHander)

