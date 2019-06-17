#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import glob
import serial
import time
import socket

# Задаем адрес сервера
SERVER_ADDRESS = ('0.0.0.0', 6767)

# Настраиваем сокет
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(SERVER_ADDRESS)
server_socket.listen(1)
print('Door and light control server is working...')


def serial_ports():
    ports = glob.glob('/dev/ttyUSB0')

    result = ports
    return result


# types: Sonar - sonar arduino, Box - box controlling arduino
# returns serial connection
def connect_to():
    while 1:
        arduinos = serial_ports()
        if arduinos:
            nano = serial.Serial(arduinos[0], 115200)
            return nano
        else:
            print("Please, connect nano to robot")
            time.sleep(10)


def action(i, nano):
    nano.write(str(i).encode())
    door = nano.readline().strip().decode("utf-8")
    if door:
        return True
    else:
        return False


if __name__ == "__main__":

    nano = None
    # nano = connect_to()
    while True:
        connection, address = server_socket.accept()
        print("new connection from {address}".format(address=address))

        data = connection.recv(1024).decode("utf-8")

        print(str(data))
        if nano:
            if action(data, nano):
                connection.send(bytes(str(data), encoding='UTF-8'))
            else:
                connection.send(bytes(str("Nano is disconnected"), encoding='UTF-8'))
        else:
            connection.send(bytes(str(data), encoding='UTF-8'))

        connection.close()
