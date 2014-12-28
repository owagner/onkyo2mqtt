#
# Bridge between the Onkyo AVR EISCP remote control protocol and MQTT.
# Allows to remotely control networked Onkyo AVRs and get status
# information.
#
# Written and (C) 2014 by Oliver Wagner <owagner@tellerulam.com>
# Provided under the terms of the MIT license
#
# Requires:
# - onkyo-eiscp - https://github.com/miracle2k/onkyo-eiscp
# - Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
#

import argparse
import logging
import time
import json
import paho.mqtt.client as mqtt
import eiscp

version="0.3"

parser = argparse.ArgumentParser(description='Bridge between onkyo-eiscp and mqtt')
parser.add_argument('--mqtt-host', default='localhost', help='MQTT server address. Defaults to "localhost"')
parser.add_argument('--mqtt-port', default='1883', type=int, help='MQTT server port. Defaults to 1883')
parser.add_argument('--mqtt-topic', default='onkyo/', help='Topic prefix to be used for subscribing/publishing. Defaults to "onkyo/"')
parser.add_argument('--onkyo-address', help='IP or hostname of the AVR. Defaults to autodiscover')
parser.add_argument('--log', help='set log level to the specified value. Defaults to WARNING. Try DEBUG for maximum detail')
args=parser.parse_args()

if args.log:
    logging.getLogger().setLevel(args.log)

topic=args.mqtt_topic
if not topic.endswith("/"):
	topic+="/"

lastSend=0

logging.info('Starting onkyo2mqtt V%s with topic prefix \"%s\"' %(version, topic))

def sendavr(cmd):
    global lastSend
    now=time.time()
    if now-lastSend<0.05:
        time.sleep(0.05-(now-lastSend))
    receiver.send(cmd)
    lastSend=time.time()
    logging.info("Sent command %s" % (cmd))

def msghandler(mqc,userdata,msg):
	try:
		global topic
		if msg.retain:
			return
		data=json.loads(msg.payload)
		if "ack" in data and data["ack"]:
			return
		cmd=data["val"]
		mytopic=msg.topic[len(topic):]
		if mytopic=="command":
			sendavr(cmd)
		else:
			llcmd=eiscp.core.command_to_iscp(mytopic+" "+cmd)
			sendvar(llcmd)
	except Exception as e:
		logging.warning("Error processing message %s" % e)

def connecthandler(mqc,userdata,rc):
    logging.info("Connected to MQTT broker with rc=%d" % (rc))
    mqc.subscribe(topic+"#",qos=1)

def disconnecthandler(mqc,userdata,rc):
    global args
    logging.warning("Disconnected from MQTT broker with rc=%d" % (rc))
    time.sleep(5)
    mqc.connect_async(args.mqtt_host,args.mqtt_port,60)

mqc=mqtt.Client()
mqc.on_message=msghandler
mqc.on_connect=connecthandler
mqc.on_disconnect=disconnecthandler
mqc.will_set(topic+"connected","{\"val\": false, \"ack\": true}",retain=True)
mqc.connect(args.mqtt_host,args.mqtt_port,60)

if args.onkyo_address:
	receiver=eiscp.eISCP(args.onkyo_address)
else:
	logging.info('Starting auto-discovery of Onkyo AVR')
	receivers=eiscp.eISCP.discover()
	if len(receivers)==0:
		logging.warning("No AVRs discovered")
		exit(1)
	elif len(receivers)!=1:
		logging.warning("More than one AVR discovered, please specify explicitely using --onkyo-address")
		exit(1)
	receiver=receivers.pop(0)
	logging.info('Discovered AVR at %s',receiver)

# Query some initial values 
for icmd in ("PWR","MVL","SLI","SLA","LMD"):
	sendavr(icmd+"QSTN")

mqc.loop_start()

def publish(suffix,val,raw):
	global topic,mqc
	robj={}
	robj["val"]=val
	if raw is not None:
	    robj["onkyo_raw"]=raw
	robj["ack"]=True
	mqc.publish(topic+suffix,json.dumps(robj),qos=1,retain=True)

publish("connected",True,None)

while True:
	msg=receiver.get(3600)
	if msg is not None:
		try:
			parsed=eiscp.core.iscp_to_command(msg)
			# Either part of the parsed command can be a list
			if isinstance(parsed[1],str):
				val=parsed[1]
			else:
				val=parsed[1][0]
			if isinstance(parsed[0],str):
				publish(parsed[0],val,msg)
			else:
				for pp in parsed[0]:
					publish(pp,val,msg)
		except:
			publish(msg[:3],msg[3:],msg)
			
