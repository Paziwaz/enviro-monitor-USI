#!/usr/bin/env python3
import argparse
import sys
import pause
from lywsd03mmc import Lywsd03mmcClient
from pms5003 import PMS5003

try:
    from ltr559 import LTR559

    ltr559 = LTR559()
except ImportError:
    import ltr559
from bme280 import BME280
import sqlite3
from sqlite3 import Error
from datetime import datetime

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()
pause.seconds(1)

sql_table_scheme = """ CREATE TABLE IF NOT EXISTS readings (
                            time datetime NOT NULL,
                            remotetemperature real NOT NULL,
                            remotehumidity real NOT NULL,
                            temperature real NOT NULL,
                            humidity real NOT NULL,
                            pressure real NOT NULL,
                            light real NOT NULL,
                            cputemperature real NOT NULL                
                        );"""

parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument("--device", "-d", help="Set the device MAC-Address in format AA:BB:CC:DD:EE:FF",
                    metavar="AA:BB:CC:DD:EE:FF")
args = parser.parse_args()


# Warms up the sensors
def initialize():
    for x in range(10):
        bme280.get_temperature()
        bme280.get_pressure()
        bme280.get_humidity()
        ltr559.get_lux()
        pause.seconds(1)


# Takes remote readings from LYWSD03MMC sensor
def take_readings_remote(client):
    data = client.data
    temperature = float(round(data.temperature, 1))
    humidity = float(round(data.humidity, 1))
    return {'remoteTemperature': temperature, 'remoteHumidity': humidity}


# Takes readings
def take_readings():
    temperature = float(round(bme280.get_temperature(), 1))
    humidity = float(round(bme280.get_humidity(), 1))
    pressure = float(round(bme280.get_pressure(), 1))
    light = float(round(ltr559.get_lux(), 1))
    return {'temperature': temperature, 'humidity': humidity, 'pressure': pressure, 'light': light}


def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = float(round((int(temp) / 1000.0), 1))
    return {'cpuTemperature': temp}


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


if __name__ == '__main__':
    mac = ""
    if args.device:
        mac = args.device
    else:
        print("Please provide your LYWSD03MMC sensor's MAC address using \'-d\' or \'--device\'")
        sys.exit(1)
    conn = sqlite3.connect("readings.db")
    create_table(conn, sql_table_scheme)
    client = Lywsd03mmcClient(mac)
    initialize()
    while True:
        remote_readings = take_readings_remote(client)
        remote_readings.update(take_readings())
        remote_readings.update(get_cpu_temperature())
        time = datetime.now().strftime("%B %d, %Y %I:%M%p")
        conn.execute("INSERT INTO readings VALUES (?,?,?,?,?,?,?,?)",
                     (time, remote_readings['remoteTemperature'], remote_readings['remoteHumidity'],
                      remote_readings['temperature'], remote_readings['humidity'],
                      remote_readings['pressure'], remote_readings['light'],
                      remote_readings['cpuTemperature']))
        conn.commit()
