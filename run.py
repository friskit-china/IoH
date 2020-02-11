from easydict import EasyDict as edict
import argparse
from modules import BME280, SSD1306, Metering
import threading
import signal
import board
import busio
import logging

import time
import os


def metering_publish_worker(_g):

    loop_sleep_time = _g.opt.iot_metering_publish_interval_sec


    metering_module = _g.modules.metering_module
    while metering_module.is_stop is not True:
        start_time = time.time()
        metering_module.update()
        end_time = time.time()
        time.sleep(loop_sleep_time - (end_time - start_time))

    pass

def bme280_update_worker(_g):
    loop_sleep_time = _g.opt.bme280_interval_sec
    bme280_module = _g.modules.bme280_module
    while bme280_module.is_stop is not True:
        start_time = time.time()
        bme280_module.update()
        end_time = time.time()
        time.sleep(loop_sleep_time - (end_time - start_time))


def ssd1306_update_worker(_g):
    loop_sleep_time = _g.opt.ssd1306_interval_sec
    ssd1306_module = _g.modules.ssd1306_module
    while _g.modules.ssd1306_module.is_stop is not True:
        start_time = time.time()
        ssd1306_module.update()
        end_time = time.time()
        time.sleep(loop_sleep_time - (end_time - start_time))


def init_logger(_g):
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler(_g.opt.logger_filename)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    logger.addHandler(handler)
    logger.addHandler(console)

    logger.warning('[Main] Logger ready')

    return logger

def main():
    _g = edict()
    parser = argparse.ArgumentParser()
    parser.add_argument('--smbus_port', type=int, default=1)
    parser.add_argument('--bme280_address', type=int, default=0x76)
    parser.add_argument('--bme280_interval_sec', type=int, default=1)
    parser.add_argument('--pwm_address', type=int, default=0x40)
    parser.add_argument('--ssd1306_address', type=int, default=0x3c)
    parser.add_argument('--ssd1306_width', type=int, default=128)
    parser.add_argument('--ssd1306_height', type=int, default=64)
    parser.add_argument('--ssd1306_interval_sec', type=int, default=1)
    parser.add_argument('--logger_filename', type=str, default='log.txt')
    parser.add_argument('--iot_host', type=str, default='cloud.thingsboard.io')
    parser.add_argument('--iot_metering_publish_interval_sec', type=int, default=2)
    _g.opt = parser.parse_args()
    _g.is_stop = False

    _g.logger = init_logger(_g)

    def exit_signal(signum, frame):
        _g.logger.warning('[Main] Finalizing')
        for module in _g.modules.values():
            module.is_stop = True
        _g.is_stop=True

    signal.signal(signal.SIGINT, exit_signal)
    signal.signal(signal.SIGTERM, exit_signal)


    _g.i2c_bus = busio.I2C(board.SCL, board.SDA)
    # init each modules
    _g.modules = dict()
    _g.modules.bme280_module = BME280(_g, _g.i2c_bus, _g.opt.bme280_address)
    _g.modules.ssd1306_module = SSD1306(_g, _g.i2c_bus, _g.opt.ssd1306_address, width=_g.opt.ssd1306_width, height=_g.opt.ssd1306_height)
    # _g.modules.metering_module = Metering(_g, _g.opt.iot_host)
    _g.modules.metering_module = Metering(_g, ioh_host=None) # use environment variable

    # multiple threading for each module
    _g.threads = dict()
    _g.threads.bme280_module_thread = threading.Thread(target=bme280_update_worker, args=(_g,))
    _g.threads.ssd1306_module_thread = threading.Thread(target=ssd1306_update_worker, args=(_g,))
    _g.threads.metering_module_thread = threading.Thread(target=metering_publish_worker, args=(_g,))

    for thread_handle in _g.threads.values():
        thread_handle.start()

    # the main loop
    while _g.is_stop is not True:
        # nothing to do now.
        time.sleep(0.1)
        pass

if __name__ == '__main__':
    print('program start')
    main()
    print('program finish')