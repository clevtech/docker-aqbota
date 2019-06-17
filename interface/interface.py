#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Bauyrzhan Ospan"
__copyright__ = "Copyright 2018, KazPostBot"
__version__ = "1.0.1"
__maintainer__ = "Bauyrzhan Ospan"
__email__ = "bospan@cleverest.tech"
__status__ = "Development"

from flask import Flask, render_template, request, Markup, jsonify
import time
import random
from random import sample
import datetime
import socket
import json
from pymongo import MongoClient
import requests
from requests import Request, Session


app = Flask(__name__)  # Creating new flask app
global passcode, timer, telegram, tripID

# Main functions

def open_door(id):
    data = str(id).replace("\n", '')
    pus = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pus.connect(('tcp-server', 6767))
    while 1:
        try:
            pus.send(bytes(str(data), encoding='UTF-8'))
            while 1:
                try:
                    ans = pus.recv(5000)
                    if ans:
                        return ans.decode('utf-8')
                except:
                    pass
        except:
            pass


def send_tlg_msg_checkpoint():
    head = "https://api.telegram.org/bot783776854:AAEYHSm-J0H8BOz1XK3irggOcGxc90K_stI/sendMessage?chat_id=-367528081&text="
    pin = ''.join(sample("0123456789", 4))
    msg = "Я приехал? Если да - ответь мне этим кодом: " + pin
    try:
        while 1:
            try:
                requests.get(head+msg)
                break
            except:
                pass
        while 1:
            time.sleep(10)
            answer = requests.get("https://api.telegram.org/bot783776854:AAEYHSm-J0H8BOz1XK3irggOcGxc90K_stI/getUpdates")
            if answer:
                text = json.loads(answer.content.decode('utf-8'))["result"][-1]["message"]["text"]
                if text == pin:
                    requests.get(head + "Okay, иду дальше по алгоритму")
                    return True
    except:
        pass


def send_tlg_msg(msg):
    head = "https://api.telegram.org/bot783776854:AAEYHSm-J0H8BOz1XK3irggOcGxc90K_stI/sendMessage?chat_id=-367528081&text="
    while 1:
        try:
            requests.get(head+msg)
            return True
        except:
            pass


def PUS_client(data):
    pus = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pus.connect(('pus-client', 8282))
    while 1:
        try:
            pus.send(bytes(str(data), encoding='UTF-8'))
            while 1:
                try:
                    ans = pus.recv(5000)
                    if ans:
                        if ans.decode('utf-8')[0] == "e":
                            continue
                        else:
                            return ans.decode('utf-8')
                except:
                    pass
        except:
            pass


# Get IP as string of the host machine
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def init_all():
    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db["config"]
    result = collection.find_one()
    global passcode
    global timer
    global telegram
    if result:
        passcode = result["passcode"]
        timer = result["timer"]
        telegram = result["tlgAPI"]
    else:
        passcode = "0605"
        timer = 20
        telegram = None


def check_weather():
    url = "http://api.apixu.com/v1/current.json?key=c02d30a45cb845dfb5863243191506&q=Astana"
    response = None
    while not response:
        try:
            response = requests.get(url)
            x = response.json()
            send_tlg_msg("Погода сейчас: " + str(x["current"]))
            print(x["current"]["temp_c"])  # > -10
            print(x["current"]["is_day"])  # == 1
            print(x["current"]["wind_kph"])  # > 50
            print(x["current"]["condition"]["code"])  # 1000, 1003, 1006, 1030
            if x["current"]["temp_c"] > -10:
                if x["current"]["is_day"] == 1:
                    if x["current"]["wind_kph"] < 50:
                        if x["current"]["condition"]["code"] in [1000, 1003, 1006, 1030]:
                            return False
                        else:
                            return "Возможны осадки, я могу повредить корпус или скользить. Статус погоды: " + \
                                   str(x["current"]["condition"]["text"])
                    else:
                        return "Ветер слишком сильный, могу сломаться из-за него. Ветер: " + \
                               str(x["current"]["wind_kph"]) + " км/час."
                else:
                    return "На данный момент уже темно. Я не могу работать, так как могу не увидеть людей."
            else:
                return "На улице не подходящие температурные условия."
        except:
            pass


# Main page
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template(
        "index.html", **locals())
# End of main page

# Admin enter page
@app.route("/login/", methods=["GET", "POST"])
def login():
    alert = "Введите пароль"
    send_tlg_msg("Кто то собирается вводить пароль")
    return render_template(
        "login.html", **locals())
# End of admin login page

# Choosing cell to load
@app.route("/robot/", methods=["GET", "POST"])
@app.route("/robot/<destination>/", methods=["GET", "POST"])
def robot(destination=None):
    global tripID
    if request.method == "POST":
        passcodenew = request.form['passcode']
        if passcode == passcodenew:
            msg = "Кто-то зашел в кабинет"
            send_tlg_msg(msg)
            return render_template(
                "destination.html", **locals())
        else:
            alert = "Вы ввели неправильный пароль"
            msg = "Кто-то пытался зайти в кабинет, используя неправильный пароль"
            send_tlg_msg(msg)
            return render_template(
                "login.html", **locals())

    if destination:
        if check_weather():
            alert = check_weather()
            return render_template(
                "error.html", **locals())

        client = MongoClient('mongodb://database:27017/')
        db = client['robot']
        collection = db["cells"]
        global tripID
        tripID = datetime.datetime.timestamp(datetime.datetime.now())
        cellID = {
            "ID": tripID,
            "created": datetime.datetime.now(),
            "destination": destination,
            "cells": [
                {
                    "package": 0,
                    "barcode": None
                },
                {
                    "package": 0,
                    "barcode": None
                },
                {
                    "package": 0,
                    "barcode": None
                },
                {
                    "package": 0,
                    "barcode": None
                }
            ]
        }


        collection.insert_one(cellID)
        result = collection.find_one({"ID": tripID})
        send_tlg_msg("Выбрали направление: " + str(destination))
        alert = "Выберите ячейку"

        cells = [0, 0, 0, 0]

        for i in range(len(cells)):
            if result["cells"][i]["package"] != 0:
                cells[i] = "Занято"
            else:
                cells[i] = "Свободно"

        cell0 = cells[0]
        cell1 = cells[1]
        cell2 = cells[2]
        cell3 = cells[3]

        return render_template(
            "robot.html", **locals())


# Choosing cell to load
@app.route("/robot/<destination>/<cellid>/", methods=["GET", "POST"])
def cell(destination, cellid):
    global tripID
    alert = "Введите ШПИ посылки для проверки."

    if request.method == "POST":
        PUSid = request.form['passcode']
        send_tlg_msg("Ввели такой ШПИ: " + str(PUSid))
        PUS = PUS_client("c/" + str(PUSid) + "/" + str(destination))
        if PUS == "1":

            client = MongoClient('mongodb://database:27017/')
            db = client['robot']
            collection = db["cells"]

            result = collection.find_one({"ID": tripID})

            cells = [0, 0, 0, 0]

            result["cells"][int(cellid[-1])]["package"] = 1
            result["cells"][int(cellid[-1])]["barcode"] = PUSid

            income = PUS_client("i/" + str(str(PUSid)))

            if income:
                income2 = json.loads(income.split("/")[1].replace("\"", "\'").replace("\'", "\""))
                alert = "Статус: " + str(income2["status"]) + ", инфо: " + str(income2["info"])
                if income[0] == "1":
                    send_tlg_msg("ШПИ норм прошел")
                    open_door(int(cellid[-1]))
                    print("Open Door")
                    collection.delete_many({"ID": tripID})
                    collection.insert_one(result)
        else:
            alert = "Не могу принять пакет для доставки, возможно есть наложенный платеж."
            send_tlg_msg("Наложка, отмена, не ссыкуй")

        client = MongoClient('mongodb://database:27017/')
        db = client['robot']
        collection = db["cells"]

        result = collection.find_one({"ID": tripID})

        for i in range(len(cells)):
            if result["cells"][i]["package"] != 0:
                cells[i] = "Занято"
            else:
                cells[i] = "Свободно"

            cell0 = cells[0]
            cell1 = cells[1]
            cell2 = cells[2]
            cell3 = cells[3]
        return render_template(
            "robot.html", **locals())
    else:
        return render_template(
            "checkpus.html", **locals())


# Choosing cell to load
@app.route("/cancel/", methods=["GET", "POST"])
def cancel():
    for i in range(4):
        open_door(i)
    send_tlg_msg("Отменил все к херам")
    alert = "Введите пароль для доступа"
    return render_template(
        "login.html", **locals())


@app.route("/sended/<destination>/", methods=["GET", "POST"])
def sended(destination):
    # TODO: send smses
    value = False
    while not value:
        value = send_tlg_msg_checkpoint()

    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db["time"]
    collection.delete_many({})
    collection.insert_one({"time_started": datetime.datetime.now()})

    return render_template(
        "give.html", **locals())


@app.route("/give/", methods=["GET", "POST"])
def give():
    global tripID
    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db["cells"]
    collection2 = db["income"]

    if request.method == "POST":
        PUSid = request.form['passcode']
        send_tlg_msg("Ввели такой пин: " + str(PUSid))


        result = collection.find_one({"ID": tripID})


        res = False
        doornum = None

        for i in range(len(result["cells"])):
            bar = result["cells"][i]["barcode"]
            pin = collection2.find_one({"barcode": bar})["pin"]
            if pin and pin == PUSid:
                res = True
                result["cells"][i]["package"] = 0
                doornum = i
                break

        if res:
            open_door(doornum)
            PUS_client("g/" + str(str(PUSid)))
            collection.delete_many({"ID": tripID})
            collection.insert_one(result)
            alert = "Возьмите посылку в открывшемся ящике. Пожалуйста, закройте его после себя."

        else:
            alert = "Неверный пин код."

    r = collection.find_one({"ID": tripID})

    p = False
    for i in range(len(result["cells"])):
        if result["cells"][i]["package"] == 1:
            p = True
            break

    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection3 = db["time"]
    t = collection3.find_one()
    time = t["time_started"]

    time2 = datetime.datetime.now()

    delta = datetime.timedelta(minutes=20)

    if (time2-time) > delta:
        p = False

    if p:
        return render_template(
            "give.html", **locals())

    else:
        send_tlg_msg_checkpoint()

        value = False
        while not value:
            value = send_tlg_msg_checkpoint()

        collection = db["cells"]
        result = collection.find_one({"ID": tripID})
        alert = "Выберите ячейку в которой осталась посылка, если нет - то нажмите на кнопку ниже."

        cells = [0, 0, 0, 0]

        for i in range(len(cells)):
            if result["cells"][i]["package"] != 0:
                cells[i] = "Есть возврат"
            else:
                cells[i] = "Свободно"

        cell0 = cells[0]
        cell1 = cells[1]
        cell2 = cells[2]
        cell3 = cells[3]

        return render_template(
            "given.html", **locals())


@app.route("/give/<cellid>/", methods=["GET", "POST"])
def give_back(cellid):
    global tripID
    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db["cells"]

    alert = "Выберите ячейку в которой осталась посылка, если нет - то нажмите на кнопку ниже."

    result = collection.find_one({"ID": tripID})

    bar = result["cells"][cellid]["barcode"]

    income = PUS_client("b/" + str(str(bar)))

    if income:
        income2 = json.loads(income.split("/")[1].replace("\"", "\'").replace("\'", "\""))
        alert = "Статус: " + str(income2["status"]) + ", инфо: " + str(income2["info"])
        if income[0] == "1":
            send_tlg_msg("Вернул товар: " + str(bar))
            open_door(cellid)
            collection.delete_many({"ID": tripID})
            collection.insert_one(result)

    cells = [0, 0, 0, 0]

    for i in range(len(cells)):
        if result["cells"][i]["package"] != 0:
            cells[i] = "Есть возврат"
        else:
            cells[i] = "Свободно"

    cell0 = cells[0]
    cell1 = cells[1]
    cell2 = cells[2]
    cell3 = cells[3]

    return render_template(
        "given.html", **locals())


# Main flask app
if __name__ == "__main__":
    init_all()
    app.run(host="0.0.0.0", port=8888, debug=True)
    # PUS_client()
