import adafruit_bme280
import adafruit_ssd1306

from easydict import EasyDict as edict

class BME280:
    def __init__(self, i2c_bus, address, sea_level_pressure=1013.25):
        self.i2c_bus = i2c_bus
        self.address = address
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c_bus, address=address)
        self.sea_level_pressure = sea_level_pressure
        self.bme280.sea_level_pressure = self.sea_level_pressure
        self.last_state = None
        self.is_stop = False
        self.update()

    def sample(self):
        state = edict()
        state.temperature = self.bme280.temperature
        state.humidity = self.bme280.humidity
        state.pressure = self.bme280.pressure
        state.altitude = self.bme280.altitude
        return state

    def update(self):
        self.last_state = self.sample()



class SSD1306:
    def __init__(self, i2c_bus, address, width, height):
        self.i2c_bus = i2c_bus
        self.address = address
        self.is_stop = False
        self.display = adafruit_ssd1306.SSD1306_I2C(width, height, self.i2c_bus, addr=address)
        self.display.fill(0)
        self.display.show()