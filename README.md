# MQTT-GPIO
A python script to poll RPi GPIO pins and subscribe and publish their state via MQTT using TLS.

This script is short and meant to be edited to the specific setup.

# Configuration
The script is edited directly, there is no separate config file.

## Polling intervall
The alternative to polling pins is to use interrupts.

Interrupts are good for very short signals and they prevent the CPU to query the level again and again, basically keeping the CPU busy. However, this can also be a downside if for instance, while switching the outputs, the inputs might briefly detect a level change, causing false or unwanted signals. Stronger pull-up or pull-down resistors than the RPIs internal ones, could be used to overcome such issues. Alternatively, just poll the inputs when the outputs are not changing state. The CPU consumption for "wastefully" polling four inputs every 100 ms is 1-3% on a RPi 1B, which is acceptable for many use cases.

The variable `POLL_INTERVALL = 0.1` configures the main loop to pause 100 ms before it checks the states again. If this is too slow or too quick for your use case, simply adjust it. The value is specified in seconds, float values are working as well. Higher values reduce CPU consumption, but increase reaction time; smaller values increase the CPU load and decrease reaction time.

## Debugging messages
To see a verbose output of what the script is doing, set the variable `PRINT_MESSAGES = True`.

## MQTT Server parameters
This script considers encryption to be mandatory.

- The variable `HOST = "server.lan"` configures the IP or FQDN (e.g. the server name).
- With `PORT = 8883` you set the port of the MQTT server. Default for encrypted MQTT connections is 8883.
- With `USERNAME = "username"` the username is set. This script expects it to be mandatory.
- With `PASSWORD = "password"` the password is set. This script expects it to be mandatory.
- With `TOPIC_PREFIX = "living_room"` the initial string of the MQTT topic is set. It really depends on your setup what is used.
- With `PAYLOAD = {True: 'ON', False: 'OFF'}` the values for True/High level of a pin and False/Low level of a pin are configured. If an input is read as "High" it corresponds to True. This mapping/dictionary will be used to convert it to the string "ON" and later publish that value. If you need to change it, adjust this dictionary. Some homeautomation-systems expect lower-case values: that would be `PAYLOAD = {True: 'on', False: 'off'}` for example.
- With `CA_CERTS = "/root/your_ca.crt"` the script gets the Root-CA-certificate. If you use self signed-certificates this is the file containing the public certificate of your Root-CA.
- The variable `CERTFILE = "/root/your_cert.crt"` is the public certificate of this server/computer the script is running on, signed by the Root-CA.
- The variable `KEYFILE = "/root/your_key.pem"` is the private, confidential key of this server/computer the script is running on. This file is not to be shared.

## Pins / GPIOs
### GPIOs as output
To configure the outputs fill the array `Outputs` with objects of class `OUTPUT`. For example you just have one GPIO-output named "Output_01" at pin 23, the array is configured: `Outputs = [OUTPUT("Output_01", 23)]`. If you have more outputs, simply add those to the array. Outputs are set from MQTT by publishing the value "ON" to the topic "living_room/Output_01/set". Note the appended "/set" in the full topic to set the value. Outputs are read from MQTT by subscribing to the topic "living_room/Output_01". The state is published when it changes.

### GPIOs as inputs
To configure the inputs fill the array `Inputs` with objects of class `INPUT`. For example you just have one GPIO-input named "Schalter_01" at pin 8, the array is configured: `Inputs = [INPUT("Schalter_01", 8)]`. If you have more inputs, simply add those to the array. Inputs are read from MQTT by subscribing to the topic "living_room/Schalter_01". The state is published when it changes.

# Dependencies
- RPi.GPIO
- paho-mqtt
