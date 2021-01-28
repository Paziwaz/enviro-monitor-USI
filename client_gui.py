#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
import matplotlib.pyplot as plt
import requests
import argparse
import ast
import tkinter
from threading import Thread

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
    window = tkinter.Tk()
    login_window = tkinter.Frame(window)
    login_window.pack()
    window.title("Enviro client")
    lbl1 = tkinter.Label(login_window, text="Podaj kod autoryzacyjny")
    lbl1.pack()
    txt = tkinter.Entry(login_window, width=10)
    txt.pack()


    def auth_click():
        auth_code = txt.get()
        try:
            is_auth_correct = requests.get(
                "http://{}:{}/{}={}".format("rpi01s", "8080", "check", auth_code)).text == "1"
        except requests.exceptions.ConnectionError:
            is_auth_correct = False
        if is_auth_correct:
            lbl1.configure(text="Zalogowane.")
            login_window.destroy()
            stats_window = tkinter.Frame(window)
            stats_window.pack()
            lbl2 = tkinter.Label(stats_window, text="Wybierz dane do generacji wykresu")
            lbl2.pack()

            def generate_temperature():
                results = get_readings("rpi01s", "8080", "temperature", auth_code)
                ylabel = "Temperatura [°C]"
                generate_graph(results, ylabel)

            but1 = tkinter.Button(stats_window, text="Temperatura", command=generate_temperature)
            but1.pack()

            def generate_temperature_predictions():
                lbl2.configure(text="Proszę czekać dane są generowane...")
                results = get_readings("rpi01s", "8080", "prediction", auth_code)
                ylabel = "Temperatura [°C]"
                lbl2.configure(text="Wybierz dane do generacji wykresu")
                generate_graph(results, ylabel)

            but2 = tkinter.Button(stats_window, text="Przewidywana temperatura",
                                  command=generate_temperature_predictions)
            but2.pack()

            def generate_humidity():
                results = get_readings("rpi01s", "8080", "humidity", auth_code)
                ylabel = "Wilgotność [%]"
                generate_graph(results, ylabel)

            but3 = tkinter.Button(stats_window, text="Wilgotność", command=generate_humidity)
            but3.pack()

            def generate_pressure():
                results = get_readings("rpi01s", "8080", "pressure", auth_code)
                ylabel = "Ciśnienie [hPa]"
                generate_graph(results, ylabel)

            but4 = tkinter.Button(stats_window, text="Ciśnienie", command=generate_pressure)
            but4.pack()

            def generate_light():
                results = get_readings("rpi01s", "8080", "light", auth_code)
                ylabel = "Światło [lux]"
                generate_graph(results, ylabel)

            but5 = tkinter.Button(stats_window, text="Światło", command=generate_light)
            but5.pack()
        else:
            lbl1.configure(text="Zły kod autoryzacyjny.")


    btn = tkinter.Button(login_window, text="Zaloguj", command=auth_click)
    btn.pack()
    window.mainloop()
