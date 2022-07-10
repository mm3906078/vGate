#!/usr/bin/python3.7
# file  -- main.py --
import logging
import signal
import subprocess
import sys
import time as t
from configparser import ConfigParser
from datetime import *
import threading
import pytz
import flask
import library

app = flask.Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("Dgate.log"),
        logging.StreamHandler()
    ]
)


class Gateway:
    speed = {}

    def __init__(self, _gw_ip, _gw_name, _gw_weight=1, _start_time=None, _end_time=None,
                 _gw_status="offline", _available=False):
        self.ip = _gw_ip
        self.weight = _gw_weight
        self.name = _gw_name
        self.status = _gw_status
        self.available = _available
        self.start_time = _start_time
        self.end_time = _end_time
        self.weight_conf = _gw_weight

    def print_available(self):
        logging.info("Gateway: {} Available: {}".format(self.name, self.available))


def runApp(host="0.0.0.0", port=5000, debug=False):
    app.run(host=host,  port=port, debug=debug)


@app.route('/sping', methods=['GET'])
def home():
    # logging.info("{}: Home page ".format(globals()[threadName]))
    speed_test()
    result = []
    for i in section:
        result.append(globals()[i].speed)
    return f"True\n{result}"


def load_config():
    logging.info("Dgate started")
    library.create_dir()
    logging.info("load config")
    config = ConfigParser()
    config.read('config.cfg')
    global section
    global time_weight
    section = config.sections()
    time_weight = config['general']['time_weight']
    section.remove("general")
    for gw in section:
        if gw != "general":
            globals()[gw] = Gateway(config[gw]['gwip'], gw, int(config[gw]['weight']),
                                    config[gw]['start_time'], config[gw]['end_time'])
    global tz
    tz = pytz.timezone(config['general']['timezone'])
    logging.info("timezone: {}".format(tz))
    logging.info("config loaded")


def startapp():
    load_config()
    switch_gateway()


def available_status():
    remove_gateway()
    for i in section:
        library.add_gateway(globals()[i].ip, globals()[i].name)
        globals()[i].state = "online"
        ping = subprocess.call(['ping', '-c', '5', '1.1.1.1'])
        if ping == 0:
            globals()[i].available = True
        else:
            globals()[i].available = False
        globals()[i].print_available()
        library.remove_gateway(globals()[i].ip, globals()[i].name)
        globals()[i].status = "offline"


def if_needed_change_weight_base_on_time():
    now = datetime.now(tz).time()
    for i in section:
        if library.in_between(now, time(int(globals()[i].start_time)), time(int(globals()[i].end_time))):
            if globals()[i].weight == globals()[i].weight_conf:
                logging.info("Gateway: {} wight is down".format(globals()[i].name))
                globals()[i].weight -= int(time_weight)
                return 1
        if not library.in_between(now, time(int(globals()[i].start_time)), time(int(globals()[i].end_time))):
            if globals()[i].weight != globals()[i].weight_conf:
                globals()[i].weight += int(time_weight)
                logging.info("Gateway: {} wight is up".format(globals()[i].name))
                return 1

    return 0


def chose_gateway():
    if_needed_change_weight_base_on_time()
    section.sort(key=lambda x: globals()[x].weight)
    available_status()
    for i in section:
        if globals()[i].available:
            logging.info("Gateway: {} is available".format(globals()[i].name))
            return globals()[i].name
    logging.warning("No gateway available")
    return None


def switch_gateway():
    gateway_list = []
    for i in section:
        gateway_list.append(globals()[i].ip)
    gateway_name = chose_gateway()
    if gateway_name is None:
        while True:
            logging.info("No gateway available, waiting for new gateway")
            gateway_name = chose_gateway()
            if gateway_name is not None:
                break
    logging.info("Switch to Gateway: {}".format(gateway_name))
    library.switch_gateway(gateway_list, globals()[gateway_name].ip, gateway_name)
    globals()[gateway_name].status = "online"


def check_gateway():
    for i in section:
        if globals()[i].status == "online":
            ping = subprocess.call(['ping', '-c', '1', '1.1.1.1'])
            if ping == 0:
                globals()[i].available = True
                logging.info("Gateway: {} checked and is available".format(globals()[i].name))
                return 0
            else:
                globals()[i].available = False
                logging.info("Gateway: {} checked and is not available".format(globals()[i].name))
                library.remove_gateway(globals()[i].ip, globals()[i].name)
                globals()[i].status = "offline"
                return 1


def always_available():
    logging.info("always_available is ruunning kkkkkkkkkkkk")
    while True:
        t.sleep(30)
        res_time_check = if_needed_change_weight_base_on_time()
        res_gateway_check = check_gateway()
        if res_time_check == 1 or res_gateway_check == 1:
            switch_gateway()


def terminate_process(signal_number, frame):
    logging.info('(SIGTERM) terminating the process')
    remove_gateway()
    sys.exit()


def read_configuration(signal_number, frame):
    logging.info('(SIGHUP) reading configuration')
    load_config()
    return


def remove_gateway():
    gateway_list = []
    for i in section:
        gateway_list.append(globals()[i].ip)
        globals()[i].status = "offline"
    library.remove_gateways(gateway_list)


def speed_test(factor='ping'):
    logging.info("Gateways are testing ... ")
    remove_gateway()
    for i in section:
        library.add_gateway(globals()[i].ip, globals()[i].name)
        globals()[i].state = "online"
        globals()[i].speed = library.speed_test()
        logging.info(globals()[i].speed)
        logging.info("Gateway: {} {} is {} ".format(globals()[i].name, factor, globals()[i].speed.get(factor)))
        library.remove_gateway(globals()[i].ip, globals()[i].name)
        globals()[i].status = "offline"

    remove_gateway()
    for i in section:
        for j in section:
            if globals()[i].speed.get(factor) < globals()[j].speed.get(factor):
                globals()[i].weight_conf -= int(time_weight)
                globals()[i].weight -= int(time_weight)
                logging.info("Gateway: {} is better than {}".format(globals()[i].name, globals()[j].name))
                break


if __name__ == '__main__':
    signal.signal(signal.SIGHUP, read_configuration)
    signal.signal(signal.SIGTERM, terminate_process)
    startapp()
    # api.app.run(host='0.0.0.0')
    t1 = threading.Thread(runApp())
    # always_available()
    t2= threading.Thread(always_available())
    t1.start()
    t2.start()
