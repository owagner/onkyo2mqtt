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
import paho.mqtt.client as mqtt
import eiscp
import logging

parser = argparse.ArgumentParser(description='Bridge between onkyo-eiscp and mqtt')
parser.add_argument('--mqtt-host', default='localhost')
parser.add_argument('--mqtt-port', default='1883', type=int)
parser.add_argument('--mqtt-topic', default='onkyo/')
parser.add_argument('--onkyo-address')
args=parser.parse_args()

topic=args.mqtt_topic
if not topic.endswith("/"):
	topic+="/"

mqc=mqtt.Client()
mqc.connect(args.mqtt_host,args.mqtt_port,60)
mqc.loop_start()

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

while True:
	msg=receiver.get(3600)
	if msg is not None:
		try:
			parsed=eiscp.core.iscp_to_command(msg)
			if isinstance(parsed[0],str):
				mqc.publish(topic+parsed[0],parsed[1],qos=1,retain=True)
			else:
				for pp in parsed[0]:
					mqc.publish(topic+pp,parsed[1],qos=1,retain=True)
		except:
			parsed=None
		logging.warning("Received %s %s" % (msg,parsed))
			
