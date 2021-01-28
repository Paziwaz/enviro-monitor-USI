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
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler


def get_from_model(filename):
    conn = sqlite3.connect("readings.db")
    dataset = pd.read_sql_query("select timestamp, remotetemperature from readings;", conn)
    conn.close()
    model = load_model(filename)
    dataset = dataset[dataset.index % 15 == 0]
    dataset = dataset.dropna(subset=["remotetemperature"])
    dataset = dataset.reset_index(drop=True)
    resultdataset = dataset.iloc[:, 1:2].values
    sc = MinMaxScaler(feature_range=(0, 1))
    sc.fit_transform(resultdataset)
    prediction = sc.transform(resultdataset)
    prediction = np.array(prediction)
    prediction = np.reshape(prediction, (prediction.shape[1], prediction.shape[0], 1))
    predicted_temperatures = model.predict(prediction)
    predicted_temperatures = sc.inverse_transform(predicted_temperatures)
    predicted_temperatures = np.reshape(predicted_temperatures, (predicted_temperatures.shape[1], predicted_temperatures.shape[0]))
    y_results = predicted_temperatures.tolist()
    last_timestamp = dataset.iloc[-1:, 0:1].values.tolist()[0][0]
    mean_timestamp_difference = int(dataset.iloc[:, 0:1].diff().mean().values.tolist()[0])
    X_results = [last_timestamp + mean_timestamp_difference * i for i in range(1, 11)]
    results = []
    for i in range(len(X_results)):
        results.append((X_results[i], y_results[i][0]))
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
        if self.path.startswith("/check="):
            auth_code = self.path.partition("=")[2]
            if check_auth_code(auth_code, ".config"):
                self.wfile.write("1".encode('utf-8'))
        if self.path.startswith("/prediction="):
            auth_code = self.path.partition("=")[2]
            if check_auth_code(auth_code, ".config"):
                results = get_from_model("model.hdf5")
                self.wfile.write(str(results).format(self.path).encode('utf-8'))
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
