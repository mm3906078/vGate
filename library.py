#!/usr/bin/python3
# file  -- library.py --
import logging
import os
import subprocess
import speedtest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("Dgate.log"),
        logging.StreamHandler()
    ]
)


def create_dir():
    if not os.path.exists("scripts"):
        os.makedirs("scripts")


def remove_dir():
    if os.path.exists("scripts"):
        os.rmdir("scripts")


def remove_gateways(gateways):
    filename = "scripts/removeGateways.sh"
    script = "#!/bin/bash\n"
    for gateway in gateways:
        script += f"route del default gw {gateway}" + "\n"
    with open(filename, "w+") as text_file:
        text_file.write(script)
    if os.path.exists(filename):
        subprocess.check_call(['chmod', '+x', filename])
        out = subprocess.call(filename)
        logging.info("Removed gateways")
        os.remove(filename)


def add_gateway(gateway, name):
    filename = "scripts/addGateway.sh"
    script = "#!/bin/bash\n"
    script += f"route add default gw {gateway}" + "\n"
    with open(filename, "w+") as text_file:
        text_file.write(script)
    if os.path.exists(filename):
        subprocess.check_call(['chmod', '+x', filename])
        out = subprocess.call(filename)
        if out == 0:
            logging.info(f"Added {name} gateway")
            os.remove(filename)
        else:
            logging.error(f"Failed to add {name} gateway")


def remove_gateway(gateway, name):
    filename = "scripts/removeGateway.sh"
    script = "#!/bin/bash\n"
    script += f"route del default gw {gateway}" + "\n"
    with open(filename, "w+") as text_file:
        text_file.write(script)
    if os.path.exists(filename):
        subprocess.check_call(['chmod', '+x', filename])
        out = subprocess.call(filename)
        if out == 0:
            logging.info(f"Removed {name} gateway")
            os.remove(filename)
        else:
            logging.error(f"Failed to remove {name} gateway")


def switch_gateway(gateways, gateway, name):
    remove_gateways(gateways)
    add_gateway(gateway, name)


def speed_test():
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download()
    return s.results.dict()


def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now < end
