#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import requests
import argparse
import ast

parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument("--auth", "-a", help="Set the authentication code for a device.",
                    metavar="J0FIHSvjxvE")
args = parser.parse_args()




def get_readings(address, port, type, auth_code):
    response = requests.get("http://{}:{}/{}={}".format(address, port, type, auth_code)).text
    updated_response = ast.literal_eval(response)
    return updated_response


def generate_graph(data, ylabel):
    y = []
    x = []
    for i in data:
        x.append(datetime.fromtimestamp(int(i[0])))
        y.append(float(i[1]))
    plt.plot(x, y)
    plt.gcf().autofmt_xdate()
    plt.ylabel(ylabel)
    plt.xlabel("Czas")
    plt.show()


if __name__ == '__main__':
    auth_code = ""
    try:
        is_auth_correct = requests.get("http://{}:{}/{}={}".format("rpi01e", "8080", "check", args.auth)).text == "1"
    except requests.exceptions.ConnectionError:
        is_auth_correct = False
    if args.auth and is_auth_correct:
        auth_code = args.auth
    else:
        print("Podany kod jest niepoprawny lub serwer jest nieosiągalny.")
        print("Proszę podaj wygenerowany przez server auth_code przy pomocy \'-a\' albo \'--auth\'")
        sys.exit(1)
    while True:
        print("Dostępne typy danych (Wybierz typ danych używając symbolu w nawiasie)\n"
              "Temperatura (T)\n"
              "Wilgotność (H)\n"
              "Ciśnienie (P)\n"
              "Światło (L)\n"
              "Przewidywanie temperatury (F)\n"
              "Wyjdź przy pomocy (Q)")
        typed_option = input("Wybierz opcję: ")
        results = []
        ylabel = ""
        if typed_option.strip().lower() == "t":
            results = get_readings("rpi01e", "8080", "temperature", auth_code)
            ylabel = "Temperatura [°C]"
        elif typed_option.strip().lower() == "h":
            results = get_readings("rpi01e", "8080", "humidity", auth_code)
            ylabel = "Wilgotność [%]"
        elif typed_option.strip().lower() == "p":
            results = get_readings("rpi01e", "8080", "pressure", auth_code)
            ylabel = "Ciśnienie [hPa]"
        elif typed_option.strip().lower() == "l":
            results = get_readings("rpi01e", "8080", "light", auth_code)
            ylabel = "Światło [lux]"
        elif typed_option.strip().lower() == "f":
            results = get_readings("rpi01e", "8080", "prediction", auth_code)
            ylabel = "Temperature [°C]"
        elif typed_option.strip().lower() == "q":
            sys.exit(1)
        generate_graph(results, ylabel)
        os.system("clear")

