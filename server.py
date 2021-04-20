#!/usr/bin/env python3

# much of this code is based on (stolen from) the examples from pimoroni

import time
import logging

from flask import Flask, jsonify
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

from bme280 import BME280, load_calibration_params

app = Flask(__name__)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("Starting API.")

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

@app.route('/light')
def get_light():
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()

    response =  {"light": lux, "lux_proximity": prox}
    logging.info(f"Response sent {response}")
    return jsonify(response)


# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = int(temp) / 1000.0
    return temp


@app.route('/temp')
def get_temp():
    factor = 2.25
    cpu_temps = [get_cpu_temperature()] * 5
    raw_temp = bme280.get_temperature()
    cpu_temp = get_cpu_temperature()
    # Smooth out with some averaging to decrease jitter
    cpu_temps = cpu_temps[1:] + [cpu_temp]
    avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = bme280.get_temperature()
    comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)

    response =  {"comp_temp": comp_temp, "cpu_temp": avg_cpu_temp, "raw_temp": raw_temp}
    logging.info(f"Response sent {response}")
    return jsonify(response)

@app.route('/pressure')
def get_pressure():
    pressure = bme280.get_pressure()

    response =  {"pressure": pressure}
    logging.info(f"Response sent {response}")
    return jsonify(response)

@app.route('/humidity')
def get_humidity():
    humidity = bme280.get_humidity()

    response =  {"humidity": humidity}
    logging.info(f"Response sent {response}")
    return jsonify(response)

@app.route('/comparison')
def get_comparison():
    port = 1
    address = 0x76
    bus = SMBus(port)

    calibration_params = load_calibration_params(bus, address)

    # the sample method will take a single reading and return a
    # compensated_reading object
    data = bme280.sample(bus, address, calibration_params)
    temp, pressure, humidity = get_temp(), get_pressure(), get_humidity()

    response =  {"temp": temp, "pressure": pressure, "humidity": humidity, "ctemp": data.temperature, "cpressure": data.pressure, "chumidity": data.humidity}
    return jsonify(response)
