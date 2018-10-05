import paho.mqtt.client as mqtt
import requests
import json

# Variables
address = "192.168.1.98:8080"
MQTT_HOST = "se2-webapp04.compute.dtu.dk"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "test"


def get_temperature():
    # Temperature rest url
    temperature_url = "http://"+address+"/rest/items/zwave_device_e0a89d4c_node2_thermostat_setpoint_heating"

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


def get_battery():
    # Battery level rest url
    battery_url = "http://"+address+"/rest/items/zwave_device_e0a89d4c_node2_battery_level"

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


def get_alarm():
    # Alarm rest url
    alarm_url = "http://"+address+"/rest/items/zwave_device_e0a89d4c_node2_alarm_general"

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


def on_publish(client, userdata, mid):
    print("Message Published...\n")


def on_connect(client, userdata, flags, rc):
    MQTT_MSG = json.dumps({"name": "Danfoss termostat",
                           "batterylevel": ""+get_battery()+"",
                           "data": ""+get_temperature()+"",
                           "unitOfMeasurement": "degrees",
                           "alarm": ""+get_alarm()+""})
    client.subscribe(MQTT_TOPIC)
    client.publish(MQTT_TOPIC, MQTT_MSG)


def on_message(client, userdata, msg):
    print("Topic: "+msg.topic)
    print(msg.payload)
    payload = json.loads(msg.payload)
    print(payload['sepalWidth'])
    client.disconnect()


# Initiate MQTT Client
mqttc = mqtt.Client()

# Register publish callback function
mqttc.on_publish = on_publish
mqttc.on_connect = on_connect
mqttc.on_message = on_message

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

# Loop forever
mqttc.loop_forever()
