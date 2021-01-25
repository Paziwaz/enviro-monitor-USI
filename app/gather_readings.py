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
import time
from sklearn.linear_model import LinearRegression
import numpy as np

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()
pause.seconds(1)

sql_table_scheme = """ CREATE TABLE IF NOT EXISTS readings (
                            timestamp numeric NOT NULL,
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


def initialize():
    print("Proceeding with EnviroPlus\'s warm up...")
    for x in range(10):
        print("Cycle {} out of 10".format(str(x + 1)))
        bme280.get_temperature()
        bme280.get_pressure()
        bme280.get_humidity()
        ltr559.get_lux()
        pause.seconds(1)
    print("Enviro is now warmed up and ready!")


def take_readings_remote(client):
    data = client.data
    temperature = float(round(data.temperature, 1))
    humidity = float(round(data.humidity, 1))
    return {'remoteTemperature': temperature, 'remoteHumidity': humidity}


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


def get_xy_values(database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT remoteTemperature, temperature, cpuTemperature FROM readings")
    results = cursor.fetchall()
    conn.close()
    temperature_correct = []
    temperature_raw = []
    temperature_cpu = []
    for i in results:
        temperature_correct.append(i[0])
        temperature_raw.append(i[1])
        temperature_cpu.append(i[2])
    x = []
    for i in range(len(temperature_cpu)):
        x.append(temperature_cpu[i] - temperature_raw[i])
    y = list(temperature_correct)
    conn.close()
    return np.array(x), np.array(y)


def generate_model(database):
    print("Generating temperature model...")
    x, y = get_xy_values(database)
    model = LinearRegression()
    model.fit(x.reshape(-1, 1), y)
    print("Model has been successfully generated!")
    return model


def create_table(database, create_table_sql):
    conn = sqlite3.connect(database)
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)
    conn.close()


if __name__ == '__main__':
    mac = ""
    db = "readings.db"
    if args.device:
        mac = args.device
    else:
        print("Please provide your LYWSD03MMC sensor's MAC address using \'-d\' or \'--device\'")
        sys.exit(1)
    create_table(db, sql_table_scheme)
    client = Lywsd03mmcClient(mac)
    initialize()
    while True:
        remote_readings = take_readings_remote(client)
        remote_readings.update(take_readings())
        remote_readings.update(get_cpu_temperature())
        timestamp = int(time.time())
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO readings VALUES (?,?,?,?,?,?,?,?)",
                     (timestamp, remote_readings['remoteTemperature'], remote_readings['remoteHumidity'],
                      remote_readings['temperature'], remote_readings['humidity'],
                      remote_readings['pressure'], remote_readings['light'],
                      remote_readings['cpuTemperature']))
        conn.commit()
        conn.close()