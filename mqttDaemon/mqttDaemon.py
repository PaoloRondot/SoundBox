import paho.mqtt.client as mqtt #import library
import subprocess
import os
import json
import requests
import base64

# Paolo RONDOT - paolo.rondot@gmail.com
# Version 1
# 20/07/2022

# IDUSER = os.environ['IDUSER']
IDUSER = "62016992f2b98c053da46e93"
 
MQTT_SERVER = "test.mosquitto.org" #specify the broker address, it can be IP of raspberry pi or simply localhost
MQTT_PORT = 8081
TOPIC_BUTTONS = "mqtt-buttonNumberClicked/" + IDUSER
TOPIC_UPDATE_PAD = "mqtt-updateTable/" + IDUSER
TOPIC_UPDATE_SOUNDS = "mqtt-updateSon/" + IDUSER
MQTT_PATH = "test_channel_Pao" #this is the name of topic, like temp
URL_COMMUN = "https://noirc01.herokuapp.com/api/"

def is_cnx_active(timeout):
    """Cette fonction permet de détecter si la raspberry est connectée à l'internet"""

    try:
        requests.head("http://www.google.com/", timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def wait_for_connection():
    """Cette fonction boucle tant qu'une connection à internet n'est pas active"""

    while True:
        if is_cnx_active(1) is True:
            # Do somthing
            print("The internet connection is active")
            break
        else:
            pass

def update_sounds():
    """Cette fonction permet de télécharger un son s'il est ajouté sur la bibliothèque en ligne
    de l'utilisateur. Il supprime également les sons existant sur la raspberry et pas en ligne"""

    wait_for_connection()
    print("update sound")
    # Fetch all sound ids
    url = URL_COMMUN + "audios/getAllWithoutDatas/" + IDUSER
    response = requests.get(url)
    if response.status_code != 200:
        print ("Error:", response.status_code)
    rep_json = response.json()

    # Fetch all sound memory
    dir_list = os.listdir("/home/pi/sounds")

    online = list()
    print(dir_list)

    # If sounds are online but not in mem -> download
    for item in rep_json:
        print(item['_id'])
        online.append(item['_id'])
        if item['_id'] not in dir_list:
            print("downloading sound " + item['_id'] + " " + item['audioName'])

            # Download the corresponding sound
            url = URL_COMMUN + "audios/byId/" + item['_id'] + '/' + IDUSER
            response_2 = requests.get(url)
            if response_2.status_code != 200:
                print ("Error:", response_2.status_code)

            data = response_2.json()
            print(data)
            b = base64.b64decode(data[0]["datas"])
            print(b)

            songFile = "/home/pi/sounds/" + item['_id']

            with open(songFile, 'wb') as output_file:
                output_file.write(b)

    # If sounds are in mem but not online -> delete the file from memory
    for item in dir_list:
        if item not in online:
            print("removing sound " + item)
            os.remove("/home/pi/sounds/" + item)


def play_button(button):
    """Cette fonction joue la musique attribué au bouton cliqué"""

    with open('/home/pi/soundbox/soundPad.txt', 'r') as f:
        lines = f.read()
    attribution = json.loads(lines)
    cmd = "(cd /home/pi/soundbox/soundManagement/ && ./a.out " + attribution[button[2:len(button)-1]] + " 0)"
    print(cmd)
    os.system(cmd)


def update_pad():
    """Cette fonction met à jour la table d'attribution (pad)"""

    wait_for_connection()
    url = URL_COMMUN + "songPad/getAll/" + IDUSER
    response = requests.get(url)
    if response.status_code != 200:
        print ("Error:", response.status_code)
    rep_text = response.text
    with open('/home/pi/soundbox/soundPad.txt', 'w') as f:
        f.write(rep_text)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    """Callback appelé à la connection de la raspberry sur le serveur MQTT"""

    print("Connected with result code "+str(rc))
 
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC_BUTTONS)
    client.subscribe(TOPIC_UPDATE_PAD)
    client.subscribe(TOPIC_UPDATE_SOUNDS)
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    """Callback appelé lorsqu'un message est reçu sur un topic"""

    print(msg.topic+" "+str(msg.payload))

    if msg.topic == TOPIC_BUTTONS:
        play_button(str(msg.payload))
    elif msg.topic == TOPIC_UPDATE_PAD:
        update_pad()
    elif msg.topic == TOPIC_UPDATE_SOUNDS:
        update_sounds()

update_sounds()
update_pad()
wait_for_connection()
client = mqtt.Client(transport='websockets')
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, MQTT_PORT)
print(IDUSER)
client.loop_forever() #use this line if you don't want to write any further code. It blocks the code forever to check for data
#client.loop_start()  #use this line if you want to write any more code here