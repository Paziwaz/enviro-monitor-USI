#!/usr/bin/env python3
import numpy as np
import pandas as pd
import sqlite3
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense,Dropout, Bidirectional

def get_data(database):
    conn = sqlite3.connect(database)
    dataset = pd.read_sql_query("select timestamp, remotetemperature from readings;", conn)
    conn.close()
    dataset = dataset[dataset.index % 15 == 0]
    return dataset


def generate_model(dataset, model_name):
    dataset = dataset.dropna(subset=["remotetemperature"])
    dataset = dataset.reset_index(drop=True)
    training_set = dataset.iloc[:, 1:2].values
    sc = MinMaxScaler(feature_range=(0, 1))
    training_set_scaled = sc.fit_transform(training_set)
    x_train = []
    y_train = []
    n_future = 10
    n_past = 500
    for i in range(0, len(training_set_scaled) - n_past - n_future + 1):
        x_train.append(training_set_scaled[i: i + n_past, 0])
        y_train.append(training_set_scaled[i + n_past: i + n_past + n_future, 0])
    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    regressor = Sequential()
    regressor.add(Bidirectional(LSTM(units=30, return_sequences=True, input_shape=(x_train.shape[1], 1))))
    regressor.add(Dropout(0.2))
    regressor.add(LSTM(units=30, return_sequences=True))
    regressor.add(Dropout(0.2))
    regressor.add(LSTM(units=30, return_sequences=True))
    regressor.add(Dropout(0.2))
    regressor.add(LSTM(units=30))
    regressor.add(Dropout(0.2))
    regressor.add(Dense(units=n_future, activation='linear'))
    regressor.compile(optimizer='adam', loss='mean_squared_error', metrics=['acc'])
    regressor.fit(x_train, y_train, epochs=5, batch_size=32)
    regressor.save(model_name)


if __name__ == '__main__':
    readings = get_data("readings.db")
    generate_model(readings, "model.hdf5")
