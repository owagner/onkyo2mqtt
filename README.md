onkyo2mqtt
==========

  Written and (C) 2015 Oliver Wagner <owagner@tellerulam.com> 
  
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
  the Onkyo EISCP protocol and command translation)
* Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
  (used for MQTT communication)


MQTT Message format
--------------------
The message format generated is a JSON encoded object with the following members:

* val - the actual value
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
the topic "\<prefix\>/status/system-power" as follows:

    {"onkyo_raw": "PWR00", "val": "standby"}

Sending commands is possible in three ways:

1. By publishing a value into a textual topic ("\<prefix\>/set/\<topic\>") with a new value
2. By publishing into the special topic "\<prefix\>/command" with a
textual command as described in https://github.com/miracle2k/onkyo-eiscp#commands
3. By publishing a raw EISCP command into the special "\<prefix\>/command" topic

A special topic "\<prefix\>/connected" is maintained. It's a enum
stating whether the module is currently running and connected to the broker
and to an AVR.


Error handling
--------------
onkyo2mqtt will terminate when it cannot establish a connection to the AVR,
or the connection dies for any reason. It will, however, reconnect to
the MQTT broker without restart.


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
    --log LOG           set log level to the specified value. Defaults to
                        WARNING. Try DEBUG for maximum detail                        
                        
Changelog
---------
* 0.4 - 2015/01/25
  - adapted to new mqtt-smarthome topic hierarchy scheme with set/ and
    status/ function prefixes, and connected being an enum

* 0.3 - 2014/12/28
  - set <prefix>/connected topic
  - add new option "--log" to set the log level
  - implement MQTT-side reconnect handling

* 0.2 - 2014/12/28
  - maintain a minimum of 50ms wait time between commands
  
