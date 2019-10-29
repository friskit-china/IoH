import os
import smbus2
from easydict import EasyDict as edict
import argparse
from modules import BME280, SSD1306
import time
import threading
import signal
import board
import busio
from PIL import ImageFont, Image, ImageDraw


def bme280_update_worker(_g):
    while _g.modules.bme280_module.is_stop is not True:
        _g.modules.bme280_module.update()
        print(_g.modules.bme280_module.last_state)
        time.sleep(0.1)

def ssd1306_update_worker(_g):
    i = 0
    font = ImageFont.load_default()
    oled = _g.modules.ssd1306_module.display
    while _g.modules.ssd1306_module.is_stop is not True:
        start_time = time.time()
        last_bme280_state = _g.modules.bme280_module.last_state

        image = Image.new('1', (oled.width, oled.height))
        draw = ImageDraw.Draw(image)

        t = time.localtime()
        text = '{y:04}/{mo:02}/{d:02} {h:02}:{mi:02}:{s:02}'.format(y=t[0], mo=t[1], d=t[2], h=t[3], mi=t[4], s=t[5])
        (font_width, font_height) = font.getsize(text)
        draw.text((oled.width / 2 - font_width / 2, 0), text, font=font, fill=255)

        text = ' Temperature:  {tm:.3f}'.format(tm=last_bme280_state.temperature)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16), text, font=font, fill=255)

        text = ' Humidity:     {tm:.3f}'.format(tm=last_bme280_state.humidity)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16 + font_height), text, font=font, fill=255)

        text = ' Pressure:   {tm:.3f}'.format(tm=last_bme280_state.pressure)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16 + font_height * 2), text, font=font, fill=255)

        text = ' Altitude:     {tm:.3f}'.format(tm=last_bme280_state.altitude)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16 + font_height * 3), text, font=font, fill=255)

        oled.image(image)
        oled.show()

        rendered_time = time.time()

        time.sleep(1 - (rendered_time - start_time))


def main():
    _g = edict()
    parser = argparse.ArgumentParser()
    parser.add_argument('--smbus_port', type=int, default=1)
    parser.add_argument('--bme280_address', type=int, default=0x76)
    parser.add_argument('--pwm_address', type=int, default=0x40)
    parser.add_argument('--ssd1306_address', type=int, default=0x3c)
    parser.add_argument('--ssd1306_width', type=int, default=128)
    parser.add_argument('--ssd1306_height', type=int, default=64)
    _g.opt = parser.parse_args()
    _g.is_stop = False

    def exit_signal(signum, frame):
        print('Finalizing')
        for module in _g.modules.values():
            module.is_stop = True
        _g.is_stop=True

    signal.signal(signal.SIGINT, exit_signal)
    signal.signal(signal.SIGTERM, exit_signal)


    _g.i2c_bus = busio.I2C(board.SCL, board.SDA)
    # init each modules
    _g.modules = dict()
    _g.modules.bme280_module = BME280(_g.i2c_bus, _g.opt.bme280_address)
    _g.modules.ssd1306_module = SSD1306(_g.i2c_bus, _g.opt.ssd1306_address,
                                        width=_g.opt.ssd1306_width, height=_g.opt.ssd1306_height)

    # multiple threading for each module
    _g.threads = dict()
    _g.threads.bme280_module_thread = threading.Thread(target=bme280_update_worker, args=(_g,))
    _g.threads.ssd1306_module_thread = threading.Thread(target=ssd1306_update_worker, args=(_g,))

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