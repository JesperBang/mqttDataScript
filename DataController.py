#!/usr/bin/env python3
#__author__ = "Jesper Bang - s144211, Sammy Masoule - s143775"
#__license__ = "GPL"
#__version__ = "1.1.0"
#__email__ = "s144211@student.dtu.dk, s143775@student.dtu.dk"
#__status__ = "Released"

import paho.mqtt.client as mqtt
import requests
import json
import re
import threading

# Variables
address = "localhost:8080"                  # Local ip of RPI used for openhab rest calls
headers = {'Content-type': 'text/plain'}    # Header for openhab rest post
MQTT_HOST = "se2-webapp04.compute.dtu.dk"   # MQTT host address
MQTT_PORT = 1883                            # MQTT Port
MQTT_KEEPALIVE_INTERVAL = 45                # MQTT keepalive
RPI_REGISTERED = False                      # Initial registration with Climify
rest_urls = []                              # Contains all possible rest urls of openhab
netatmo_device_ids = []                     # Contains all ID's of netatmo devices
zwave_device_ids = []                       # Contains all ID's of zwave devices
temperature_endpoint = []                   # Endpoints for temperature rest url
battery_endpoint = []                       # Endpoiunts for battery rest url
sensor_id = []                              # Sensor id's
counter = 0


# Get uuid serial number of the arm processor
def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        # Open file with RPI hardware info
        fp = open('/proc/cpuinfo','r')
        line = fp.readline()

        # Find line with CPU UUID and extract it
        while line:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
            line = fp.readline()

        # Close resources
        fp.close()
    except:
        # Error handling
        cpuserial = "ERROR000000000"

    return cpuserial


# Registration of RPI on Climify
def register_rpi():
    global RPI_REGISTERED
    # Try to register as long as registration fails
    while not RPI_REGISTERED:
        # Create json payload
        json_body = {
                "UUID": getserial()
            }

        # Post request to climify api and save response
        response = post_actuator("api-post-rpi.php", json_body)

        # Response handling
        if response == 200:
            # Success handling - set rpi to registered state
            RPI_REGISTERED = True
            print("RPI connected with: " + str(response))
        else:
            # Error handling - (something went bad)
            print("Error with code: "+str(response))


# Happens when we connect to MQTT broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {0}".format(str(rc)))
    client.subscribe(getserial()+"/#")


# Happens when we receive message
def on_message(client, userdata, msg):
    print("Message received-> " + msg.topic + " " + str(msg.payload))
    print(msg.topic + " is equal to " + "{}/Get/Devices".format(getserial()))
    handle_message(msg)


# Happens when MQTT message is published
def on_publish(client, userdata, mid):
    print("Message Published...\n")


# Message handler
def handle_message(msg):
    # Topics
    _accept_topic = "{}/Accept/Devices".format(getserial())
    _get_devices_topic = "{}/Get/Devices".format(getserial())
    _disconnect_topic = "{}/Disconnect/Devices".format(getserial())
    _temperature_topic = "{}/Commands".format(getserial())
    _response_topic = "{}/Response".format(getserial())

    if msg.topic == _accept_topic:
        # Method for accepting device
        print("Devices Acceptance requested")
        accept_devices(msg)

    if msg.topic == _disconnect_topic:
        # Method for disconnecting device
        print("Device Disconnect requested")
        disconnect_devices(msg)

    if msg.topic == _get_devices_topic:
        # Method initialises device search on rpi
        print("Device search requested")
        search_devices()

        # Method fetches devices from rpi inbox
        print("Device inbox requested")
        fetch_inbox()

    if msg.topic == _temperature_topic:
        # Method for setting temperature of actuator
        print("Temperature change requested")
        change_temperature(msg)


# Accept devices in openhab
def accept_devices(msg):
    print("Accepting Device")

    # Create json payload
    json_data = json.loads(msg.payload)
    print(json_data['UUID'])

    # Accept devices rest url
    device_url = "http://" + address + "/rest/inbox/" + json_data['UUID'] + "/approve"

    # Handling response
    response = requests.post(device_url)
    print(repr(response.reason))

    # If sensor was accepted then notify climify api
    if repr(response.reason).__contains__("OK"):
        uuid = json_data['UUID']
        create_data = "{\n" + "\"UniqueID\": " + "\"" + uuid + "\"" "\n}"
        data = json.loads(create_data)
        post_actuator("api-change-actuator-status", data)


# Disconnect devices from openhab
def disconnect_devices(msg):
    print("Disconnect Device")

    # Create payload
    json_data = json.loads(msg.payload)
    print(json_data['UUID'])

    # Disconnect device rest url
    device_url = "http://" + address + "/rest/things/" + json_data['UUID']

    # Handling response
    response = requests.delete(device_url)
    print(repr(response.reason))


def search_devices():
    # Discover devices on z-wave binding
    print("Start zwave discovery")
    search_url = "http://" + address + "/rest/discovery/bindings/zwave/scan"
    #Posting to webapp
    searchresp = requests.post(search_url)
    print(repr(searchresp))


def fetch_inbox():
    # Fetch the found devices
    print("Fetching inbox data")

    # Temperature rest url
    device_url = "http://" + address + "/rest/inbox"

    # Creating request for devices
    response = requests.get(device_url, headers=headers)
    print(repr(response))

    # Data handling
    tempvar = json.loads(response.content)

    label = tempvar[0]['label']

    genericclass = tempvar[0]['properties']['zwave_class_generic']

    thinguid = tempvar[0]['thingUID']

    # response in json
    create_data = "{\n" + "\"label\": " + "\"" + label + "\"" + ",\n" + \
                          "\"zwave_class_generic\": " + "\"" + genericclass + "\"" + ",\n" + \
                          "\"thingUID\": " + "\"" + thinguid + "\"" + ",\n" + \
                          "\"serial\": " + "\"" + getserial() + "\"" + "\n}"

    data = json.loads(create_data)
    print(data)
    post_actuator("api-post-actuators", data)


def change_temperature(msg):
    print("Change temperature\n")
    get_temperature_endpoint()

    # Splitting message to get requested device and temperature
    json_data = json.loads(msg.payload)
    temperature = json_data['value']
    deviceid = json_data['device']
    deviceid = str(deviceid.replace(":", "_"))

    # Searching the list of possible endpoints with deviceid
    for item in temperature_endpoint:
        if deviceid in item:
            endpoint = item
            print("item: " + item + "\n")

    # Received following payload
    print("Endpoint: " + str(endpoint) + "\ndeviceid: " + str(deviceid) + "\ntemperature: " + str(temperature) + "\n")

    # Temperature rest url
    # temperature_url = "http://" + address + "/rest/items/zwave_device_e0a89d4c_node2_thermostat_setpoint_heating"
    temperature_url = "http://" + address + "/rest/items/" + endpoint

    # Creating request for set temperature
    response = requests.post(temperature_url, data=str(temperature), headers=headers)
    print(repr(response))


def get_temperature(endpoint):
    # Temperature rest url
    # Access openhab rest api on address and grab the device temperature
    print("http://"+address+"/rest/items/"+endpoint)
    temperature_url = "http://"+address+"/rest/items/"+endpoint

    # Creating request for temperature
    temperature_req = requests.get(temperature_url)
    resp_dict = json.loads(temperature_req.content)

    # Requesting json object called "state" containing the temperature variable
    temperature = resp_dict.get('state')

    # Printing the variable to console
    print("Rest temperature call data:")
    print((repr(temperature_req.status_code) + " " + temperature_req.reason + ":\n" + temperature_req.content.decode()))
    print("State: "+temperature+"\n")
    return temperature


def get_battery(endpoint):
    # Battery level rest url
    battery_url = "http://"+address+"/rest/items/"+endpoint

    # Creating request for battery level
    battery_req = requests.get(battery_url)
    resp_dict = json.loads(battery_req.content)

    # Requesting json object called "state" containing the battery level variable
    battery = resp_dict.get('state')

    # Printing the variable to console
    print("Rest battery call data:")
    print((repr(battery_req.status_code) + " " + battery_req.reason + ":\n" + battery_req.content.decode()))
    print("State: "+battery+"\n")
    return battery


def get_alarm(endpoint):
    # Alarm rest url
    alarm_url = "http://"+address+"/rest/items/"+endpoint

    # Creating request for alarm
    alarm_req = requests.get(alarm_url)
    resp_dict = json.loads(alarm_req.content)

    # Requesting json object called "state" containing the alarm variable
    alarm = resp_dict.get('state')

    # Printing the variable to console
    print("Rest alarm call data:")
    print((repr(alarm_req.status_code) + " " + alarm_req.reason + ":\n" + alarm_req.content.decode()))
    print("State: "+alarm+"\n")
    return alarm


# Posting to climify api
def post_actuator(endpoint, data):
    if "api-change-actuator-status" in endpoint:
        requests.post("http://se2-webapp04.compute.dtu.dk/api/api-change-actuator-status.php", data)
    if "api-post-actuators" in endpoint:
        requests.post("http://se2-webapp04.compute.dtu.dk/api/api-post-actuators.php", data)
    if "api-post-rpi.php" in endpoint:
        r = requests.post("http://se2-webapp04.compute.dtu.dk/api/api-post-rpi.php", data)
        return r.status_code


# Posting temperature every 30 sec
def send_temperature():
    get_temperature_endpoint()
    print("Sending temperature")

    # Send data over MQTT for each device which posts temperatures
    for devices in range(0, len(find_index_of_key(rest_urls, "heat"))):
        MQTT_MSG = "%s,building=\"101\" Temperature=%s,batterylvl=%s,uuid=\"%s\"" % (sensor_id[devices], get_temperature(temperature_endpoint[devices]), get_battery(battery_endpoint[devices]), getserial())
        client.publish("TempData", MQTT_MSG)


def get_temperature_endpoint():
    # Clear variables
    del sensor_id[:]
    del battery_endpoint[:]
    del temperature_endpoint[:]

    # Looping through the array returning endpoint position of all thermostat devices
    for thermostat in find_index_of_key(rest_urls, "heat"):
        # Trimming the device name to fit string format (cutting out \']) from the end.
        cap = len(rest_urls[thermostat]) - 2
        # Applying the trim to the front as well.
        temperature_endpoint.append(rest_urls[thermostat][3:cap])

    # Looping through the array returning the endpoint position of battery info of all thermostat devices
    for battery in find_index_of_key(rest_urls, "battery"):
        # Trimming the device name to fit string format (cutting out \']) from the end.
        cap = len(rest_urls[battery])-2
        # Applying the trim to the front as well.
        battery_endpoint.append(rest_urls[battery][3:cap])

    # Looping through the array returning the device id of all thermostat devices
    for sensorid in find_index_of_key(rest_urls, "heat"):
        # Splitting on underscore since thats the default openhab formatting
        sensor_id.append(str(rest_urls[sensorid]).split("_")[2])

    # Printing to log
    print("-----Got following endpoints-----")
    print(temperature_endpoint)
    print(battery_endpoint)
    print(sensor_id)
    print("---------------------------------")


# Fetch all possible rest url's
def get_rest_endpoints():
    # Clear variables
    del rest_urls[:]
    del netatmo_device_ids[:]
    del zwave_device_ids[:]

    # Fetch the found devices
    print("Fetching rest url's\n")

    # Temperature rest url
    device_url = "http://" + address + "/rest/things"

    # Creating request for devices
    response = requests.get(device_url, headers=headers)

    # Data handling
    bridgeUID = find_values("bridgeUID", response.content)
    print("-----Fetching device id's-----")

    # Finding all UUID's of netatmo and zwave devices
    for items in bridgeUID:
        if items.split(":")[0] in "netatmo":
            netatmo_device_ids.append(items.split(":")[2])
        if items.split(":")[0] in "zwave":
            zwave_device_ids.append(items.split(":")[2])

    print("Netatmo rest: "+str(netatmo_device_ids)+"\n")
    print("zwave rest: " + str(zwave_device_ids) + "")
    print("-----####################-----\n")

    # Now find all the possible rest urls
    values = find_values("linkedItems", response.content)

    # All possible rest url's
    for url in values:
        if url:
            rest_urls.append(str(url))
    print("-----All possible rest url's-----")
    print(str(rest_urls)+"\n")
    print(find_index_of_key(rest_urls, "heat"))


def find_index_of_key(array, key):
    x = array
    get_indexes = lambda x, xs: [i for (y, i) in zip(xs, range(len(xs))) if x in y]
    return get_indexes(key, x)


# strips json from linkedItems values and returns result
def find_values(key, json_data):
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[key])
        except KeyError:
            pass
        return a_dict

    json.loads(json_data, object_hook=_decode_dict)  # Return value ignored.
    return results


# Thread to handle timer for sending temperature every 30 sec
def run_script():
    # Send MQTT message every 30 sec
    try:
        print("Sending temperature")
        get_rest_endpoints()
        threading.Timer(30.0, send_temperature()).start()
    except TypeError:
        print("No actuator found")

    # Recursively calling itself
    threading.Timer(30.0, run_script).start()


# Connection
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
run_script()
register_rpi()

# Blocking
client.loop_forever()
