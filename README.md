# MQTT DataController

## DataController.py
School project based on a master's project. Connecting sensors to read CO2 levels, humidity and temperate and acting upon the data, i.e. opening a window if it's too cold.
Current progress: Recieving information from sensors and forwarding the data to the webapp. Furthermore the script can now recieve commands and act upon them. Sensors can be added and removed from openhab when the GUI on the webapp requests this.

## Authors
Jesper Bang - s144211 & Sammy Masoule - s143775.

## License
Licenced under GPL.

## Contact
Email:    s144211@student.dtu.dk & s143775@student.dtu.dk

## Release
Status:   Release v. 1.0.1

## mqttSend.py & mqttRecv.py
(Early version of DataController script not used anymore)

mqttSend.py fetches data from sensor over REST and publish it on MQTT.

mqttRecv.py recieves messages send from skoleklima over MQTT.
