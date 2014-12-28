onkyo2mqtt
==========

  Written and (C) 2014 Oliver Wagner <owagner@tellerulam.com> 
  
  Provided under the terms of the MIT license.

Overview
--------
  
Bridge between the Onkyo AVR EISCP remote control protocol and MQTT.
Allows to remotely control networked Onkyo AVRs and get status
information.

It's intended as a building block in heterogenous smart home environments where 
an MQTT message broker is used as the centralized message bus. See 
https://github.com/mqtt-smarthome for a rationale and architectural overview.


Prerequisites
-------------

* Python 2.7+
* onkyo-eiscp - https://github.com/miracle2k/onkyo-eiscp (implements
  the Onkyo EISCP protocol)
* Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
  (used for MQTT communication)


MQTT Message format
--------------------

The message format accepted and generated is a JSON encoded object with the following members:

* val - the actual value
* ack - when sending messages, onkyo2mqtt sets this to _true_. If this is set to _true_ on incoming messages, they
  are ignored, to avoid loops.
* onkyo_raw - the raw EISCP command before parsing by onkyo-eiscp  


Command parsing and topics
--------------------------
The onkyo-eiscp module by miracle2k provides sophisticated parsing which
translated the raw EISCP commands into readable strings. Please see the
module page at https://github.com/miracle2k/onkyo-eiscp for more
information about that.

onkyo2mqtt will translate incoming EISCP status events into their
textual representation, and publish those via MQTT.

For example, the raw "power is off" status is published into 
the topic "\<prefix\>/system-power" as follows:

    {"onkyo_raw": "PWR00", "ack": true, "val": "standby"}

Sending commands is possible in three ways:

1. By publishing a value into a textual topic with a new value
2. By publishing into the special topic "\<prefix\>/command" with a
textual command as described in https://github.com/miracle2k/onkyo-eiscp#commands
3. By publishing a raw EISCP command into the special "\<prefix\>/command" topic


Usage
-----

    --mqtt-host MQTT_HOST
                        MQTT server address. Defaults to "localhost"
    --mqtt-port MQTT_PORT
                        MQTT server port. Defaults to 1883
    --mqtt-topic MQTT_TOPIC
                        Topic prefix to be used for subscribing/publishing.
                        Defaults to "onkyo/"
    --onkyo-address ONKYO_ADDRESS
                        IP or hostname of the AVR. Defaults to autodiscover
                        
                        
