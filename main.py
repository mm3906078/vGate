#!/usr/bin/python3
# file  -- main.py --
import logging
import subprocess
import time as t
from configparser import ConfigParser
from datetime import *
import pytz

import library

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("Dgate.log"),
        logging.StreamHandler()
    ]
)


class Gateway:
    def __init__(self, _gw_ip, _gw_name, _gw_weight=1, _start_time=None, _end_time=None,
                 _gw_status="offline", _available=False):
        self.ip = _gw_ip
        self.weight = _gw_weight
        self.name = _gw_name
        self.status = _gw_status
        self.available = _available
        self.start_time = _start_time
        self.end_time = _end_time

    def print_available(self):
        logging.info("Gateway: {} Available: {}".format(self.name, self.available))


def startapp():
    logging.info("Dgate started")
    library.create_dir()
    logging.info("load config")
    config = ConfigParser()
    config.read('config.cfg')
    global section
    section = config.sections()
    section.remove("general")
    for gw in section:
        if gw != "general":
            globals()[gw] = Gateway(config[gw]['gwip'], gw, int(config[gw]['weight']),
                                    config[gw]['start_time'], config[gw]['end_time'])
    global tz
    tz = pytz.timezone(config['general']['timezone'])
    logging.info("timezone: {}".format(tz))
    logging.info("config loaded")
    switch_gateway()


def available_status():
    gateway_list = []
    for i in section:
        gateway_list.append(globals()[i].ip)
        globals()[i].status = "offline"
    library.remove_gateways(gateway_list)
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


def chose_gateway():
    now = datetime.now(tz).time()
    logging.info("Current time: {}".format(now))
    for i in section:
        if library.in_between(now, time(int(globals()[i].start_time)), time(int(globals()[i].end_time))):
            logging.info("Gateway: {} wight is down".format(globals()[i].name))
            globals()[i].weight -= 1
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
    while True:
        t.sleep(20)
        res = check_gateway()
        if res == 1:
            switch_gateway()


startapp()
always_available()
