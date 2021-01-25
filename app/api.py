#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import sqlite3
import os
import secrets
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor


# HARDCODED FUNCTION
def decision_tree_prediction():
    conn = sqlite3.connect("readings.db")
    weather_df = pd.read_sql_query("select timestamp, remotetemperature from readings;", conn)
    conn.close()
    weather_y = weather_df.pop("remotetemperature")
    weather_X = weather_df
    train_X, test_X, train_y, test_y = train_test_split(weather_X, weather_y, test_size=0.2, random_state=4)
    regressor = DecisionTreeRegressor(random_state=0)
    regressor.fit(train_X, train_y)
    prediction3 = regressor.predict(test_X)
    np.mean((prediction3 - test_y) ** 2)
    last_timestamp = weather_X["timestamp"].max()
    new_timestamps = [last_timestamp + (i * 60) for i in range(1440)]
    results = []
    for timestamp in new_timestamps:
        results.append((new_timestamps, float(regressor.predict(np.array(timestamp).reshape(-1, 1))[0])))
    return results


def generate_auth_code(config_path):
    auth_code = secrets.token_urlsafe(8)
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    config = open(config_path + "/auth_code", "w+")
    config.write(auth_code)
    print("Generated auth code: {}".format(auth_code))


def get_auth_code(config_path):
    return open(config_path + "/auth_code", "r").readline()


def check_auth_code(auth_code, config_path):
    return auth_code == get_auth_code(config_path)


def get_from_db(database, item):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, {} FROM readings order by timestamp desc limit 10000".format(item))
    results = cursor.fetchall()
    conn.close()
    return results


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        if self.path.startswith("/temperature="):
            auth_code = self.path.partition("=")[2]
            if check_auth_code(auth_code, ".config"):
                results = get_from_db("readings.db", "remotetemperature")
                self.wfile.write(str(results).format(self.path).encode('utf-8'))
        if self.path.startswith("/humidity="):
            auth_code = self.path.partition("=")[2]
            if check_auth_code(auth_code, ".config"):
                results = get_from_db("readings.db", "humidity")
                self.wfile.write(str(results).format(self.path).encode('utf-8'))
        if self.path.startswith("/pressure="):
            auth_code = self.path.partition("=")[2]
            if check_auth_code(auth_code, ".config"):
                results = get_from_db("readings.db", "pressure")
                self.wfile.write(str(results).format(self.path).encode('utf-8'))
        if self.path.startswith("/light="):
            auth_code = self.path.partition("=")[2]
            if check_auth_code(auth_code, ".config"):
                results = get_from_db("readings.db", "light")
                self.wfile.write(str(results).format(self.path).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    from sys import argv

    generate_auth_code(".config")
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
