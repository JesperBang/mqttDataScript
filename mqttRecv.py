import paho.mqtt.client as mqtt
import requests
import re

# Variables
address = "192.168.1.98:8080"
headers = {'Content-type': 'text/plain'}


def on_connect(client, userdata, flags, rc):
    print("Connected with result code {0}".format(str(rc)))
    client.subscribe("test")
    client.subscribe("Temperature")


def on_message(client, userdata, msg):
    print("Message received-> " + msg.topic + " " + str(msg.payload))
    handle_message(msg)


def handle_message(msg):
    if msg.topic in "Temperature":
        print(repr(msg.payload))
        command = find_numbers(repr(msg.payload))
        print(command[0])

        # Temperature rest url
        temperature_url = "http://" + address + "/rest/items/zwave_device_e0a89d4c_node2_thermostat_setpoint_heating"

        # Creating request for set temperature
        response = requests.post(temperature_url, data=repr(command[0]), headers=headers)
        print(repr(response))


def find_numbers(string, ints=True):
    numexp = re.compile(r'[-]?\d[\d,]*[\.]?[\d{2}]*')
    numbers = numexp.findall(string)
    numbers = [x.replace(',','') for x in numbers]
    if ints is True:
        return [int(x.replace(',','').split('.')[0]) for x in numbers]
    else:
        return numbers


# Connection
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("se2-webapp04.compute.dtu.dk", 1883, 60)

# Blocking
client.loop_forever()
