#
# Bridge between an Onkyo AVR controlled with the EISCP protocol
# and MQTT
#
# Written by Oliver Wagner <owagner@tellerulam.com>
#
# Requires:
# - onkyo-eiscp - https://github.com/miracle2k/onkyo-eiscp
# - Eclipse paho for Python - http://www.eclipse.org/paho/clients/python/
#

import argparse
import logging
import json
import paho.mqtt.client as mqtt
import eiscp

parser = argparse.ArgumentParser(description='Bridge between onkyo-eiscp and mqtt')
parser.add_argument('--mqtt-host', default='localhost', help='MQTT server address. Defaults to "localhost"')
parser.add_argument('--mqtt-port', default='1883', type=int, help='MQTT server port. Defaults to 1883')
parser.add_argument('--mqtt-topic', default='onkyo/', help='Topic prefix to be used for subscribing/publishing. Defaults to "onkyo/"')
parser.add_argument('--onkyo-address', help='IP or hostname of the AVR. Defaults to autodiscover')
args=parser.parse_args()

topic=args.mqtt_topic
if not topic.endswith("/"):
	topic+="/"

def msghandler(mqc,userdata,msg):
	try:
		global topic,receiver
		if msg.retain:
			return
		data=json.loads(msg.payload)
		if "ack" in data and data["ack"]:
			return
		cmd=data["val"]
		mytopic=msg.topic[len(topic):]
		if mytopic=="command":
			receiver.send(cmd)
		else:
			llcmd=eiscp.core.command_to_iscp(mytopic+" "+cmd)
			receiver.send(llcmd)
	except Exception as e:
		logging.warning("Error processing message %s" % e)

mqc=mqtt.Client()
mqc.connect(args.mqtt_host,args.mqtt_port,60)
mqc.subscribe(topic+"#",qos=1)
mqc.on_message=msghandler

if args.onkyo_address:
	receiver=eiscp.eISCP(args.onkyo_address)
else:
	logging.info('Starting auto-discover of Onkyo AVR')
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
receiver.send("PWRQSTN")
receiver.send("MVLQSTN")
receiver.send("SLIQSTN")
receiver.send("SLAQSTN")
receiver.send("LMDQSTN")

mqc.loop_start()

def publish(suffix,val,raw):
	global topic,mqc
	robj={}
	robj["val"]=val
	robj["onkyo_raw"]=raw
	robj["ack"]=True
	mqc.publish(topic+suffix,json.dumps(robj),qos=1,retain=True)

while True:
	msg=receiver.get(3600)
	if msg is not None:
		try:
			parsed=eiscp.core.iscp_to_command(msg)
			# Either part can be a list
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
			
