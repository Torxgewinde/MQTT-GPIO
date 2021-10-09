#!/usr/bin/python

########################################################################
#
# MQTT + RPi GPIO script
#
# (c) 2021 Tom Stöveken
# 
# License: GPLv3 ff
#
# This python script polls RPi GPIO pins and subscribes and pusblishes
# their state via MQTT. It uses TLS to secure the network connection.
#
########################################################################

import RPi.GPIO as GPIO
import time
from paho.mqtt.client import (Client, MQTT_ERR_SUCCESS)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

PRINT_MESSAGES = False
POLL_INTERVALL = 0.1

########################################################################
class OUTPUT(object): 
	def __init__(self, name, pin): 
		self.__gpio = pin
		self.__name = name
		GPIO.setup(self.__gpio, GPIO.OUT)
		self.__state = (GPIO.input(self.__gpio) == 1)

	def set(self,state):
		log("[output set]: %s to %d" % (self.__name, state))
		self.__state = state

	def get(self):
		log("[output get]: %s is %d" % (self.__name, self.__state))
		return self.__state

	def changed(self):
		result = (GPIO.input(self.__gpio) == 1) != self.__state
		if result:
			log("[output changed]: %s" % (self.__name))
		return result

	def name(self):
		return self.__name

	def commit(self):
		log("[output commit]: %s is %d" % (self.__name, self.__state))
		GPIO.output(self.__gpio, self.__state)

class INPUT(object): 
	def __init__(self, name, pin, debounce=300):
		self.__name = name
		self.__gpio = pin
		GPIO.setup(self.__gpio, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
		self.__state = (GPIO.input(self.__gpio) == 1)

	def get(self):
		log("[input get]: %s is %d" % (self.__name, self.__state))
		return self.__state

	def changed(self):
		result = (GPIO.input(self.__gpio) == 1) != self.__state
		if result:
			log("[input changed]: %s" % (self.__name))
		return result

	def name(self):
		return self.__name

	def commit(self):
		self.__state = (GPIO.input(self.__gpio) == 1)
		log("[input commit]: %s is %d" % (self.__name, result))

########################################################################

def connect(client, username, password, ca_certs, certfile, keyfile, host, port):
	#if connection is still there just return
	if client.is_connected():
		return True

	#use TLS even in internal networks
	client.username_pw_set(username, password=password)
	client.tls_set(	ca_certs=ca_certs,
					certfile=certfile,
					keyfile=keyfile)
	client.tls_insecure_set(False)
	client.connect(host, port=port)
	client.loop_start()

	#wait a few seconds to connect
	for i in range(5):
		if client.is_connected():
			return True
		time.sleep(1)

	return False

def on_message(client, userdata, message):
	global PAYLOAD_INVERSE

	log("[On_Message]: " + message.topic +":"+ message.payload.decode() + ", "+str(PAYLOAD_INVERSE[message.payload.decode()]))

	try:
		for out in Outputs:
			if TOPIC_PREFIX+"/output/"+out.name()+"/set" == message.topic:
				out.set(PAYLOAD_INVERSE[message.payload.decode()])
	except Exception as e:
		log("[ERROR] {}".format(e))

def log(message):
	global PRINT_MESSAGES
	if PRINT_MESSAGES:
		print(message)

########################################################################
if __name__ == '__main__':

	HOST = "server.lan"
	PORT = 8883
	USERNAME = "username"
	PASSWORD = "password"
	TOPIC_PREFIX = "living_room"
	PAYLOAD = {True: 'ON', False: 'OFF'}

	CA_CERTS = "/root/your_ca.crt"
	CERTFILE = "/root/your_cert.crt"
	KEYFILE = "/root/your_key.pem"

	Outputs = [OUTPUT("Output_01", 23), \
		OUTPUT("Output_02", 11), \
		OUTPUT("Output_03", 15), \
		OUTPUT("Output_04", 21), \
		OUTPUT("Output_05", 19), \
		OUTPUT("Output_06", 18), \
		OUTPUT("Output_07", 26), \
		OUTPUT("Output_08", 22), \
		OUTPUT("Output_09", 24), \
		OUTPUT("Output_10", 13), \
		OUTPUT("Output_11", 3), \
		OUTPUT("Output_12", 5), \
		OUTPUT("Output_13", 7)]

	Inputs = [INPUT("Schalter_01", 8), \
		INPUT("Schalter_02", 10), \
		INPUT("Schalter_03", 16), \
		INPUT("Schalter_04", 12)]
		
	client = Client()
	client.on_message=on_message
	subscribed = False

	global PAYLOAD_INVERSE
	PAYLOAD_INVERSE = dict((a, b) for b, a in PAYLOAD.items())

	#main loop
	while True:
		log("[Loop]: %s" % time.ctime())
		time.sleep(POLL_INTERVALL)

		#connect to MQTT, only proceed if connected
		if not connect(client, USERNAME, PASSWORD, CA_CERTS, CERTFILE, KEYFILE, HOST, PORT):
			log("[ERROR]: Connection failed, retrying")
			subscribed = False
			time.sleep(1.0)
			continue

		#iterate over all outputs, subscribe to MQTT topics
		if not subscribed:
			#assume subscribing succeeds, any error will cause to est. subscriptions again
			subscribed = True
			for out in Outputs:
				try:
					log("[Subscribe]: "+TOPIC_PREFIX+"/output/"+out.name()+"/set")
					(result, mid) = client.subscribe(TOPIC_PREFIX+"/output/"+out.name()+"/set", qos=2)
					if result != MQTT_ERR_SUCCESS:
						log("Subscribing failed for " + out.name())
						subscribed = False
				except Exception as e:
					log("[ERROR] {}".format(e))
					subscribed = False

		#iterate over all outputs, publish changes via MQTT
		for out in Outputs:
			if out.changed():
				try:
					client.publish(TOPIC_PREFIX+"/output/"+out.name(), PAYLOAD[out.get()], qos=2, retain=True)
				except Exception as e:
					log("[ERROR] {}".format(e))

		#iterate over all inputs, publish MQTT if state changed
		for inp in Inputs:
			if inp.changed():
				log("[CHANGE]: "+inp.name()+": "+PAYLOAD[inp.get()])
				try:
					client.publish(TOPIC_PREFIX+"/input/"+inp.name(), PAYLOAD[inp.get()], qos=2, retain=True)
				except Exception as e:
					log("[ERROR] {}".format(e))

		#sync states of script and hardware now
		for outp in Outputs:
			outp.commit()
		for inp in Inputs:
			inp.commit()

	GPIO.cleanup()
