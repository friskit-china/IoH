import adafruit_bme280
import adafruit_ssd1306
import paho.mqtt.client as mqtt
import json
import os
from PIL import ImageFont, Image, ImageDraw
import time

from easydict import EasyDict as edict

class BME280:
    def __init__(self, _g, i2c_bus, address, sea_level_pressure=1013.25):
        _g.logger.info('[BME280] Initialization')
        self._g = _g
        self.i2c_bus = i2c_bus
        self.address = address
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c_bus, address=address)
        self.sea_level_pressure = sea_level_pressure
        self.bme280.sea_level_pressure = self.sea_level_pressure
        self.last_state = None
        self.is_stop = False
        self.update()
        self._g.logger.info('[BME280] Ready')

    def sample(self):
        state = edict()
        state.temperature = self.bme280.temperature
        state.humidity = self.bme280.humidity
        state.pressure = self.bme280.pressure
        state.altitude = self.bme280.altitude
        return state

    def update(self):
        try:
            self.last_state = self.sample()
            self._g.logger.info('[BME280] Last State: ' + str(self.last_state))
        except Exception as e:
            self._g.logger.error('[BME280] Err: ' + str(e))



class SSD1306:
    def __init__(self, _g, i2c_bus, address, width, height):
        _g.logger.info('[SSD1306] Initialization')
        self._g = _g
        self.i2c_bus = i2c_bus
        self.address = address
        self.is_stop = False
        self.display = adafruit_ssd1306.SSD1306_I2C(width, height, self.i2c_bus, addr=address)
        self.display.fill(0)
        self.display.show()
        self.font = ImageFont.load_default()
        self._g.logger.info('[SSD1306] Ready')

    def update(self):
        last_bme280_state = self._g.modules.bme280_module.last_state

        image = Image.new('1', (self.display.width, self.display.height))
        draw = ImageDraw.Draw(image)

        t = time.localtime()
        text = '{y:04}/{mo:02}/{d:02} {h:02}:{mi:02}:{s:02}'.format(y=t[0], mo=t[1], d=t[2], h=t[3], mi=t[4], s=t[5])
        (font_width, font_height) = self.font.getsize(text)
        draw.text((self.display.width / 2 - font_width / 2, 0), text, font=self.font, fill=255)

        text = ' Temperature:  {tm:.3f}'.format(tm=last_bme280_state.temperature)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16), text, font=self.font, fill=255)

        text = ' Humidity:     {tm:.3f}'.format(tm=last_bme280_state.humidity)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16 + font_height), text, font=self.font, fill=255)

        text = ' Pressure:   {tm:.3f}'.format(tm=last_bme280_state.pressure)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16 + font_height * 2), text, font=self.font, fill=255)

        text = ' Altitude:     {tm:.3f}'.format(tm=last_bme280_state.altitude)
        # (font_width, font_height) = font.getsize(text)
        draw.text((0, 16 + font_height * 3), text, font=self.font, fill=255)

        self.display.image(image)
        self.display.show()


class Metering:
    def __init__(self, _g, iot_host):
        _g.logger.info('[Metering] Initialization')
        if 'METERING_ACCESS_TOKEN' not in os.environ:
            _g.logger.error('[Metering] Undefined Access Token')
            raise ValueError('Undefined Access Token')

        self._g = _g
        self.is_stop = False
        self.client = mqtt.Client()

        self.access_token = os.environ['METERING_ACCESS_TOKEN']
        self.iot_host = iot_host
        self.client.username_pw_set(self.access_token)
        self.client.connect(iot_host)
        self.client.loop_start()

        self._g.logger.info('[Metering] Ready')

    def update(self):
        try:
            self.publish_metering()
        except Exception as e:
            self._g.logger.warning('[Metering] Exception when publish: ', str(e))
        pass

    def publish_metering(self):
        last_bme280_state = self._g.modules.bme280_module.last_state
        sensor_data = {
            'temperature': last_bme280_state.temperature,
            'humidity': last_bme280_state.humidity,
            'pressure': last_bme280_state.pressure
        }

        publish_message = json.dumps(sensor_data)
        self.client.publish('v1/devices/me/telemetry', publish_message, 1)
        self._g.logger.info('[Metering] Published message: ' + publish_message)


