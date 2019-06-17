__author__ = "Bauyrzhan Ospan"
__copyright__ = "Copyright 2018, Aqbota"
__version__ = "1.0.1"
__maintainer__ = "Bauyrzhan Ospan"
__email__ = "bospan@cleverest.tech"
__status__ = "Development"

import requests
import xml.dom.minidom
import datetime
from pprint import pprint
import re
from pymongo import MongoClient
from random import sample
import socket
import json
import os


def send_post(url, data, headers):
    while 1:
        try:
            res = requests.post(url, data, headers)
            break
        except:
            print("Сервер не дает ответа, пробую еще раз")
    return res


def save_db(log, name):
    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db[name]
    try:
        collection.insert_one(log)
    except:
        try:
            del log["_id"]
        except KeyError:
            pass
    print("===========================================")
    print("Сохранил в логи следующее: ")
    pprint(log)
    print("===========================================")
    print()


def take_db(barcode, name):
    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db[name]
    result = collection.find_one({"barcode": barcode})
    return result


def find_db(name, dic):
    client = MongoClient('mongodb://database:27017/')
    db = client['robot']
    collection = db[name]
    result = collection.find_one(dic)
    print(dic)
    print(result)
    return result


def printxml(res):
    pretyy = xml.dom.minidom.parseString(res.content)
    pretty_xml_as_string = pretyy.toprettyxml()
    print(pretty_xml_as_string)


def pus_data(barcode, address):
    barcode = barcode.replace("\n", "")
    address = address.replace("\n", "")
    url = "http://pls-test.post.kz/api/service/postamatHierarchy?wsdl"
    url2 = "http://pls-test.post.kz/api/service/postamat?wsdl"

    headers = {'content-type': 'text/xml'}

    file_name = "./templates/GETDATA.xml"
    file_name2 = "./templates/chech_money.xml"

    with open(file_name, "r") as file:
        req = file.read()
        req = req.replace("BARCODE", barcode)
        print("=================================================")
        print("Отправляю запрос для получения данных о посылке на url: " + str(url))
        print()
        pprint(req)
        print("--------------------------------------------------")

    response = send_post(url, data=req.replace("\n", "").encode('utf-8'), headers=headers)

    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    printxml(response)
    print("--------------------------------------------------")


    with open(file_name2, "r") as file:
        req = file.read()
        req = req.replace("BARCODE", barcode)
        print("=================================================")
        print("Отправляю запрос для получения данных о наложке на url: " + str(url2))
        print()
        pprint(req)
        print("--------------------------------------------------")

    response2 = send_post(url2, data=req.replace("\n", "").encode('utf-8'), headers=headers)
    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    printxml(response2)
    print("--------------------------------------------------")

    cash_check = re.findall("<ns2:amount>(.*?)</ns2:amount>", str(response2.content))
    if cash_check:
        if cash_check[0] != "0":
            cash_check = False
        else:
            cash_check = True
    else:
        cash_check = True

    log = {
        "address": address,
        'barcode': barcode,
        "client": re.findall("<Rcpn>(.*?)</Rcpn>", str(response.content.decode("utf-8")))[0],
        "time": datetime.datetime.now(),
        "phone": re.findall("<RcpnPhone>(.*?)</RcpnPhone>", str(response.content.decode("utf-8")))[0],
        "cash check": cash_check
    }

    save_db(log, "data")

    if cash_check:
        return True
    else:
        return False


def income(barcode):
    barcode = barcode.replace("\n", "")
    url = "http://pls-test.post.kz/api/service/postamat?wsdl"

    headers = {'content-type': 'text/xml'}

    file_name = "./templates/INCOME.xml"

    with open(file_name, "r") as file:
        req = file.read()
        req = req.replace("BARCODE", barcode)
        print("=================================================")
        print("Отправляю запрос на хранение посылки на url: " + str(url))
        print()
        pprint(req)
        print("--------------------------------------------------")

    response = send_post(url, data=req.replace("\n", "").encode('utf-8'), headers=headers)
    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    printxml(response)
    print("--------------------------------------------------")


    status = re.findall("<ns3:code>(.*?)</ns3:code>", str(response.content.decode("utf-8")))[0]

    info = re.findall("<ns3:name>(.*?)</ns3:name>", str(response.content.decode("utf-8")))[0]

    pin = ''.join(sample("0123456789", 6))

    log = find_db("data", {"barcode": barcode})

    log["status"] = status
    log["info"] = info
    log["pin"] = pin
    log["income_time"] = datetime.datetime.now()

    save_db(log, "income")

    return status, info, pin


def given(barcode):
    barcode = barcode.replace("\n", "")
    url = "http://pls-test.post.kz/api/service/postamat?wsdl"

    headers = {'content-type': 'text/xml'}

    file_name = "./templates/given.xml"

    with open(file_name, "r") as file:
        req = file.read()
        req = req.replace("BARCODE", barcode)
        print("=================================================")
        print("Отправляю запрос на выдачу посылки на url: " + str(url))
        print()
        pprint(req)
        print("--------------------------------------------------")

    response = send_post(url, data=req.replace("\n", "").encode('utf-8'), headers=headers)
    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    printxml(response)
    print("--------------------------------------------------")

    status = re.findall("<ns3:code>(.*?)</ns3:code>", str(response.content.decode("utf-8")))[0]

    info = re.findall("<ns3:name>(.*?)</ns3:name>", str(response.content.decode("utf-8")))[0]

    log = {
        "status": status,
        "info": info,
        "barcode": barcode,
        "time": datetime.datetime.now()
    }

    save_db(log, "given")

    return status, info


def back(barcode):
    barcode = barcode.replace("\n", "")
    url = "http://pls-test.post.kz/api/service/postamat?wsdl"

    headers = {'content-type': 'text/xml'}

    file_name = "./templates/given.xml"

    with open(file_name, "r") as file:
        req = file.read()
        req = req.replace("BARCODE", barcode)
        print("=================================================")
        print("Отправляю запрос на возврат посылки на url: " + str(url))
        print()
        pprint(req)
        print("--------------------------------------------------")

    response = send_post(url, data=req.replace("\n", "").encode('utf-8'), headers=headers)
    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    printxml(response)
    print("--------------------------------------------------")

    status = re.findall("<ns3:code>(.*?)</ns3:code>", str(response.content.decode("utf-8")))[0]

    info = re.findall("<ns3:name>(.*?)</ns3:name>", str(response.content.decode("utf-8")))[0]

    log = {
        "status": status,
        "info": info,
        "barcode": barcode,
        "time": datetime.datetime.now()
    }

    printxml(response)

    save_db(log, "back")

    return status, info


def send_sms(barcode):

    results = []
    for bar in barcode:
        results.append(find_db("income", {"barcode": bar.replace("\n", "")}))

    place = find_db("data", {"barcode": barcode[0]})["address"]

    # url = "http://92.46.190.22:8080/altsmsgate/altsmsgate.wsdl"
    url = "http://92.46.190.22:8080/smsgate/?wsdl"
    headers = {'content-type': 'text/xml'}
    # file_name = "./templates/sms.xml"
    # text = "Робот почтальон приехал доставить Вам посылку [barcode]. Он ждет вас в [place] до [time]." \
    #        " Введите [pin] для получения доступа на дисплее робота."
    # body = "<sch:Sms>" \
    #         "<sch:SmsText>[text]</sch:SmsText>" \
    #         "<sch:TelegramText>[text]</sch:TelegramText>" \
    #         "<sch:PostKzText>[text]</sch:PostKzText>" \
    #         "<sch:PhoneNumber>[phone]</sch:PhoneNumber>" \
    #         "</sch:Sms>"
    file_name = "./templates/sms_new.xml"

    text = "Robot-kyrer ozhidaet Vas, polychite vashy posilky. Vremya ozhidaniya 20 minyt."

    body = "<element><phoneNumber>[phone]</phoneNumber><message>[text]</message></element>"

    with open(file_name, "r") as file:
        req = file.read()

    time = (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")

    bodies = ""

    for i in range(len(barcode)):
        text0 = text
        text1 = text0.replace("[time]", time) \
            .replace("[pin]", results[i]["pin"]).replace("[place]", place).replace("[barcode]", barcode[i])
        body2 = body.replace("[text]", text1).replace("[phone]", results[i]["phone"])
        bodies += body2

    request = req.replace("[body]", bodies)
    response = send_post(url, data=request.replace("\n", "").encode('utf-8'), headers=headers)

    print("=================================================")
    print("Отправляю запрос смс посылки на url: " + str(url))
    print()
    pprint(request)
    print("--------------------------------------------------")
    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    printxml(response)
    print("--------------------------------------------------")

    # ids = re.findall("SmsId>([0-9]+)</ns2:AltSms", str(response.content.decode("utf-8")))
    # statuses = re.findall("AltSmsStatus>(.*?)</ns2:AltSmsStatus", str(response.content.decode("utf-8")))

    ids = re.findall("sId>([0-9]+)</sms", str(response.content.decode("utf-8")))
    statuses = re.findall("<status>(.*?)</status>", str(response.content.decode("utf-8")))

    smses = []

    log = {
        "place": place,
        "sms": [],
        "time": datetime.datetime.now()
    }

    try:
        for i in range(len(barcode)):
            smses.append({"phone": results[i]["phone"], "pin": results[i]["pin"], "barcode": barcode[i], "status": statuses[i], "smsid": ids[i]})
    except:
        for i in range(len(barcode)):
            smses.append({"phone": results[i]["phone"], "pin": results[i]["pin"], "barcode": barcode[i], "status": None, "smsid": ids[i]})

    log["sms"] = smses

    save_db(log, "sms")


def send_sms_save(barcode):

    results = []
    for bar in barcode:
        results.append(find_db("income", {"barcode": bar.replace("\n", "")}))

    place = find_db("data", {"barcode": barcode[0]})["address"]

    url = "http://92.46.190.22:8080/smsgate/?wsdl"
    # url = "http://92.46.190.22:8080/altsmsgate/altsmsgate.wsdl"
    headers = {'content-type': 'text/xml'}
    # file_name = "./templates/sms.xml"
    # text = "Ваша посылка [barcode] передана роботу-курьеру на хранение, " \
    #        "в ближайшее время ожидайте доставку по адресу [place]"
    # body = "<sch:Sms>" \
    #         "<sch:SmsText>[text]</sch:SmsText>" \
    #         "<sch:TelegramText>[text]</sch:TelegramText>" \
    #         "<sch:PostKzText>[text]</sch:PostKzText>" \
    #         "<sch:PhoneNumber>[phone]</sch:PhoneNumber>" \
    #         "</sch:Sms>"

    file_name = "./templates/sms_new.xml"

    text = "[time] Vam postupila posylka [barcode] " \
           "peredano robot-kyrer: [place]" \
           "Kod dostupa [pin]. V blizhaishee vremya ozhidaite."

    body = "<element><phoneNumber>[phone]</phoneNumber><message>[text]</message></element>"

    with open(file_name, "r") as file:
        req = file.read()


    time = (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d")

    bodies = ""

    for i in range(len(barcode)):
        text0 = text
        text1 = text0.replace("[time]", time) \
            .replace("[pin]", results[i]["pin"]).replace("[place]", place).replace("[barcode]", barcode[i])
        body2 = body.replace("[text]", text1).replace("[phone]", results[i]["phone"])
        bodies += body2

    request = req.replace("[body]", bodies)
    response = send_post(url, data=request.replace("\n", "").encode('utf-8'), headers=headers)

    print("=================================================")
    print("Отправляю запрос смс хранения на url: " + str(url))
    print()
    pprint(request)
    print("--------------------------------------------------")
    print("=================================================")
    print("Принял ответ от сервера: ")
    print()
    try:
        printxml(response)
    except:
        print(response)
    print("--------------------------------------------------")

    # ids = re.findall("SmsId>([0-9]+)</ns2:AltSms", str(response.content.decode("utf-8")))
    # statuses = re.findall("AltSmsStatus>(.*?)</ns2:AltSmsStatus", str(response.content.decode("utf-8")))

    ids = re.findall("sId>([0-9]+)</sms", str(response.content.decode("utf-8")))
    statuses = re.findall("<status>(.*?)</status>", str(response.content.decode("utf-8")))

    smses = []

    log = {
        "place": place,
        "sms": [],
        "time": datetime.datetime.now()
    }

    try:
        for i in range(len(barcode)):
            smses.append(
                {"phone": results[i]["phone"], "pin": results[i]["pin"], "barcode": barcode[i], "status": statuses[i],
                 "smsid": ids[i]})
    except:
        for i in range(len(barcode)):
            smses.append({"phone": results[i]["phone"], "pin": results[i]["pin"], "barcode": barcode[i], "status": None,
                          "smsid": ids[i]})

    log["sms"] = smses

    save_db(log, "sms_save")


def diagnostics():
    print("Удаляю старые данные с Базы Данных:")
    client = MongoClient('mongodb://database:27017/')
    client.drop_database('robot')
    print("Начало теста: " + str(datetime.datetime.now()))
    print("########################################")
    print()
    print()
    print("########################################")
    print("Проверка посылки")
    print("########################################")
    print()
    print()
    phone = pus_data("KZ160621000KZ", "Astana HUB")
    print()
    print()
    print("########################################")
    print("Хранение посылки")
    print("########################################")
    print()
    print()
    status, info, pin = income("KZ160621000KZ")
    print()
    print()
    print("########################################")
    print("СМС о хранении посылки")
    print("########################################")
    print()
    print()
    send_sms_save(["KZ160621000KZ"])
    print()
    print()
    print("########################################")
    print("СМС о доставке посылки")
    print("########################################")
    print()
    print()
    send_sms(["KZ160621000KZ"])
    print()
    print()
    print("########################################")
    print("Вручение посылки клиенту")
    print("########################################")
    print()
    print()
    given("KZ160621000KZ")
    print()
    print()
    print("########################################")
    print("Тест сценария возврата курьеру: хранение посылки")
    print("########################################")
    print()
    print()
    income("KZ160621000KZ")
    print()
    print()
    print("########################################")
    print("Тест сценария возврата курьеру: возврат")
    print("########################################")
    print()
    print()
    back("KZ160621000KZ")
    print()
    print()
    print("########################################")
    print("Конец теста: " + str(datetime.datetime.now()))
    print("########################################")
    print()
    print()


if __name__ == "__main__":

    SERVER_ADDRESS = ('0.0.0.0', 8282)
    # Настраиваем сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    print('PUS client server is working')

    while True:
        connection, address = server_socket.accept()
        print("new connection from {address}".format(address=address))

        data = connection.recv(1024).decode('utf-8')
        if data:
            if data[0] == "c":
                try:
                    if pus_data(data.split("/")[1], data.split("/")[2]):
                        connection.send(bytes(str("1"), encoding='UTF-8'))
                    else:
                        connection.send(bytes(str("0"), encoding='UTF-8'))
                except:
                    connection.send(bytes(str("e"), encoding='UTF-8'))

            elif data[0] == "i":
                try:
                    status, info, pin = income(data.split("/")[1])
                    if status[0] == "e" or status[0] == "E":
                        answer = "0/" + str({"status": status, "pin": pin, "info": info})
                        connection.send(bytes(str(answer), encoding='UTF-8'))
                    else:
                        answer = "1/" + str({"status": status, "pin": pin, "info": info})
                        connection.send(bytes(str(answer), encoding='UTF-8'))
                except:
                    connection.send(bytes(str("e"), encoding='UTF-8'))

            elif data[0] == "g":
                try:
                    status, info = given(data.split("/")[1])
                    if status[0] == "e" or status[0] == "E":
                        answer = "0/" + str({"status": status, "info": info})
                        connection.send(bytes(str(answer), encoding='UTF-8'))
                    else:
                        answer = "1/" + str({"status": status, "info": info})
                        connection.send(bytes(str(answer), encoding='UTF-8'))
                except:
                    connection.send(bytes(str("e"), encoding='UTF-8'))

            elif data[0] == "b":
                try:
                    status, info = back(data.split("/")[1])
                    if status[0] == "e" or status[0] == "E":
                        answer = "0/" + str({"status": status, "info": info})
                        connection.send(bytes(str(answer), encoding='UTF-8'))
                    else:
                        answer = "1/" + str({"status": status, "info": info})
                        connection.send(bytes(str(answer), encoding='UTF-8'))
                except:
                    connection.send(bytes(str("e"), encoding='UTF-8'))

            elif data[0] == "s":
                request = json.loads(data.split("/")[1])
                try:
                    send_sms(request)
                    connection.send(bytes(str("1"), encoding='UTF-8'))
                except:
                    connection.send(bytes(str("e"), encoding='UTF-8'))

            elif data[0] == "k":
                request = json.loads(data.split("/")[1])
                try:
                    send_sms_save(request)
                    connection.send(bytes(str("1"), encoding='UTF-8'))
                except:
                    connection.send(bytes(str("e"), encoding='UTF-8'))

        connection.close()
    # print(os.system("ls -al"))
    # diagnostics()
