import paho.mqtt.client as mqtt #import library
import subprocess
import os
 
MQTT_SERVER = "public.mqtthq.com" #specify the broker address, it can be IP of raspberry pi or simply localhost
MQTT_PATH = "test_channel_Pao" #this is the name of topic, like temp
 
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
 
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    cmd = "(cd /home/pi/soundbox/soundManagement/ && ./a.out " + str(msg.payload)[2:len(str(msg.payload))-1] + " 0)"
    print(cmd)
    os.system(cmd)
    # more callbacks, etc
 
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER)
#print("yoyo")
client.loop_forever() #use this line if you don't want to write any further code. It blocks the code forever to check for data
#client.loop_start()  #use this line if you want to write any more code here