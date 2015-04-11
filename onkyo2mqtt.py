#
# Bridge between the Onkyo AVR EISCP remote control protocol and MQTT.
# Allows to remotely control networked Onkyo AVRs and get status
# information.
#
# Written and (C) 2015 by Oliver Wagner <owagner@tellerulam.com>
# Provided under the terms of the MIT license
#
# Requires:
# - onkyo-eiscp - https://github.com/miracle2k/onkyo-eiscp
# - Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
#

import argparse
import logging
import logging.handlers
import time
import json
import paho.mqtt.client as mqtt
import eiscp

version="0.5"

parser = argparse.ArgumentParser(description='Bridge between onkyo-eiscp and MQTT')
parser.add_argument('--mqtt-host', default='localhost', help='MQTT server address. Defaults to "localhost"')
parser.add_argument('--mqtt-port', default='1883', type=int, help='MQTT server port. Defaults to 1883')
parser.add_argument('--mqtt-topic', default='onkyo/', help='Topic prefix to be used for subscribing/publishing. Defaults to "onkyo/"')
parser.add_argument('--onkyo-address', help='IP or hostname of the AVR. Defaults to autodiscover')
parser.add_argument('--log', help='set log level to the specified value. Defaults to WARNING. Try DEBUG for maximum detail')
parser.add_argument('--syslog', action='store_true', help='enable logging to syslog')
args=parser.parse_args()

if args.log:
    logging.getLogger().setLevel(args.log)
if args.syslog:
    logging.getLogger().addHandler(logging.handlers.SysLogHandler())

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
		mytopic=msg.topic[len(topic):]
		if mytopic=="command":
			sendavr(msg.payload)
		elif mytopic[0:4]=="set/":
			llcmd=eiscp.core.command_to_iscp(mytopic[4:]+" "+msg.payload)
			sendavr(llcmd)
	except Exception as e:
		logging.warning("Error processing message %s" % e)

def connecthandler(mqc,userdata,rc):
    logging.info("Connected to MQTT broker with rc=%d" % (rc))
    mqc.subscribe(topic+"set/#",qos=0)
    mqc.subscribe(topic+"command",qos=0)
    mqc.publish(topic+"connected",2,qos=1,retain=True)

def disconnecthandler(mqc,userdata,rc):
    logging.warning("Disconnected from MQTT broker with rc=%d" % (rc))
    time.sleep(5)

mqc=mqtt.Client()
mqc.on_message=msghandler
mqc.on_connect=connecthandler
mqc.on_disconnect=disconnecthandler
mqc.will_set(topic+"connected",0,qos=2,retain=True)
mqc.connect(args.mqtt_host,args.mqtt_port,60)
mqc.publish(topic+"connected",1,qos=1,retain=True)

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
	mqc.publish(topic+"status/"+suffix,json.dumps(robj),qos=0,retain=True)

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
			
