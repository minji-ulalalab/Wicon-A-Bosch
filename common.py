import configparser
import socket
import time
from datetime import datetime
import pymysql
import pymysql.cursors
from logger import logger
from collections import OrderedDict

config = configparser.ConfigParser()
config.read('config.ini')
prev_time = time.time()
wp_idx = None
wv_idx = None
wu_idx = None


def socket_connect():
    """
    socket setting for IP4v, TCP/IP
    return sock(object set socket) to main
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.connect((config.get('controller', 'ip'), config.getint('controller', 'port')))
    return sock


def send_data_to_controller(sock, msg):
    """
    send message to controller
    client send the request message to controller
    :return: 0 , error> -1
    """
    global prev_time
    try:
        logger.debug("Send message")
        sock.send(msg)
        logger.info("[Sent]" + str(msg))
        prev_time = time.time()
        return 0
    except Exception as e:
        logger.error("send data error : " + str(e))
        return -1


def time_check():
    """
    check the time from last communication.
    :return: if the time is over than 6 > True, else > False
    """
    global prev_time
    try:
        period = time.time() - prev_time
        if period > 6:
            return True
        else:
            return False

    except Exception as e:
        logger.error("time check error : " + str(e))


def setting_data(mid, echo_data):
    """
    set new variables from the data
    MID==0002, if MID of data is 0002, the data has information about controller
    (serial number, type etc ...)
    MID==0061, if MID of data is 0061, the data has information about tightening
    (torque, angle, pset number etc ...)
    :return: 0 , error> -1
    """
    global wp_idx, wv_idx, wu_idx

    if mid == "0002":
        logger.info("tightening data: " + str(echo_data))
        tightening_info = mid_0002_parsing(echo_data)

        try:
            if tightening_info["serial_flag"]:
                logger.info("controller type check.... %s..ok" % tightening_info["controller_serial"])
                wp_idx = tightening_info['wp_idx']
                wv_idx = tightening_info['wv_idx']
                wu_idx = tightening_info['wu_idx']  # user idx
                return 0
            else:
                logger.info("controller information is not match")
                raise Exception

        except Exception as e:
            logger.error("data check error : " + str(e))
            return -1

    elif mid == "0061":
        tightening_data = mid_0061_parsing(echo_data)

        torque = tightening_data["torque"]
        # torque_max = tightening_data["torque_max_limit"]
        angle = tightening_data["angle"]
        # angle_max = tightening_data["angle_max"]
        wd_set = tightening_data["tightening_program_number"]
        wd_status = tightening_data["tightening_status"]
        now = datetime.now()
        update_time = now.strftime('%Y-%m-%d %H:%M:%S')

        print("[torque] = " + tightening_data["torque"])
        print("[torque_max] = " + tightening_data["torque_max_limit"])
        print("[angle] = " + tightening_data["angle"])
        print("[angle_max] = " + tightening_data["angle_max"])
        print("[wd_set] = " + tightening_data["tightening_program_number"])
        print("[wd_status] = " + tightening_data["tightening_status"])

        if wd_status == "1":
            logger.info("tightening........OK")
        else:
            logger.info("tightening.......NOK")

        insert_data_to_db = (wp_idx, wv_idx, wu_idx, torque, '10', angle, '0.0', wd_set, wd_status, update_time,
                      update_time)
        insert_query(insert_data_to_db)

    else:
        pass


def db_connect():
    """
    create object to connect the touchPC database
    :return: connection(object to connect), error> -1
    """
    try:
        logger.debug("start to create database connection")
        connection = pymysql.connect(
            user=config.get('database', 'user'),
            password=config.get('database', 'password'),
            port=config.getint('database', 'port'),
            host=config.get('database', 'host'),
            database=config.get('database', 'database'),
            cursorclass=pymysql.cursors.DictCursor
        )
        ret = connection

    except Exception as e:
        logger.error("database connect error : " + str(e))
        ret = -1

    finally:
        return ret


def select_query(controller_serial):
    """
    select query of database about information of controller connected using serial
    :return: the cursor.fetchall
    """
    connection = db_connect()
    sql = "SELECT * FROM wi_virtual_station a LEFT JOIN wi_power_focus b ON a.wp_idx = b.wp_idx \
                WHERE b.wp_serial = " + "'" + controller_serial + "'"
    with connection.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql)
        ret = cur.fetchall()
        print(ret)
        return ret
        logger.info('ret: ' + str(ret))


def insert_query(tightening_data):
    """
    insert query to database about information of tightening
    """
    try:
        connection = db_connect()
        sql = """insert into `wi_pf_data` (wp_idx, wv_idx, 
                                  wu_idx, wd_torque, wd_torque_max, wd_angle,
                                  wd_angle_max,wd_set,wd_status, wd_update_date, wd_create_date)
         values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        """
        val = tightening_data
        cur = connection.cursor()
        cur.execute(sql, val)
        connection.commit()
        logger.info("sending ok")
        connection.close()

    except Exception as e:
        logger.error("insert fail" + str(e))


def mid_0061_parsing(data_0061):
    """
    parsing data from 0061 cf. Atlas open protocol document
    :return: dic_data
    """
    logger.debug("parsing data from tightening")
    dic_data = OrderedDict()

    dic_data["cell_id"] = data_0061[22:26]
    dic_data["channel_id"] = data_0061[28:30]
    dic_data["torque_controller_name"] = data_0061[32:57]
    dic_data["id_code"] = data_0061[59:84]
    dic_data["job_number"] = data_0061[86:88]
    dic_data["tightening_program_number"] = data_0061[92:93]
    dic_data["ok_counter_limit"] = data_0061[95:99]
    dic_data["ok_counter_value"] = data_0061[101:105]
    dic_data["tightening_status"] = data_0061[107:108]
    dic_data["torque_status"] = data_0061[110:111]
    dic_data["angle_status"] = data_0061[113:114]
    dic_data["torque_min_limit"] = str(data_0061[118:120]) + "." + str(data_0061[120:122])
    dic_data["torque_max_limit"] = str(data_0061[126:128]) + "." + str(data_0061[128:130])
    dic_data["target_torque"] = data_0061[132:138]
    dic_data["torque"] = str(data_0061[142:144]) + "." + str(data_0061[144:146])
    dic_data["angle_min"] = data_0061[148:153]
    dic_data["angle_max"] = data_0061[155:160]
    dic_data["target_angle"] = data_0061[162:167]
    dic_data["angle"] = data_0061[173:174]
    dic_data["time_stamp"] = data_0061[177:195]

    return dic_data


def mid_0002_parsing(data_0002):
    """
    parsing data from mid 0002
    :return: dic_data
    """
    logger.debug("parsing data from communication")
    dic_data = OrderedDict()

    dic_data["controller_serial"] = "510000922"

    controller_serial = dic_data["controller_serial"]
    ret = select_query(controller_serial)

    for db_data in ret:
        dic_data["wp_idx"] = str(db_data['wp_idx'])  # power focus idx
        dic_data["wv_idx"] = str(db_data['wv_idx'])  # virtual station idx
        dic_data["wu_idx"] = str(db_data['wu_idx'])  # user idx
        dic_data["db_serial"] = str(db_data['wp_serial'])

    if dic_data["controller_serial"] == dic_data["db_serial"]:
        dic_data["serial_flag"] = True
    else:
        dic_data["serial_flag"] = False

    return dic_data




