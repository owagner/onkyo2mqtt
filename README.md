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
                        
                        
