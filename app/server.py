#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import sqlite3
import os
import secrets
import sys


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
    cursor.execute("SELECT time, {} FROM readings".format(item))
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
                results = get_from_db("readings.db", "realtemperature")
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
