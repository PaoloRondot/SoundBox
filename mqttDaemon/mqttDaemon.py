import paho.mqtt.client as mqtt #import library
import subprocess
import os
import json
import requests
import base64
import multiprocessing
import random
import time
import RPi.GPIO as GPIO
import datetime
import pyttsx3

engine = pyttsx3.init()

# Paolo RONDOT - paolo.rondot@gmail.com
# Version 1
# 20/07/2022

# TODO Faire en sorte depuis le service de lancement au boot que l'on ait accès à la variable d'environnement IDUSER

conf_file = open("/home/pi/SoundBox/conffile.json.conf", "r")
conf = json.load(conf_file)

# IDUSER = os.environ['IDUSER']
# IDUSER = "64429949d35dee5ae5c96997"
IDUSER = conf["IDUSER"]

MQTT_SERVER = "hairdresser.cloudmqtt.com" #specify the broker address, it can be IP of raspberry pi or simply localhost
MQTT_PORT = 35759
MQTT_USERNAME = "pcveijdg"
MQTT_PASSWORD = "QbEEywSkudq5"

TOPIC_PLAYLIST = "newPlaylist/" + IDUSER
TOPIC_PLAYLIST_DEL = "deletePlaylist/" + IDUSER
TOPIC_SOUND_P = "newSongInPlaylist/" + IDUSER
TOPIC_SOUND_DEL = "deleteSong/" + IDUSER
TOPIC_RANDOM_P = "randomPlaylist/" + IDUSER
TOPIC_PLAY = "playPlaylist/" + IDUSER
TOPIC_SITE_CONNECTION = "connectedSB/" + IDUSER + "/check"
TOPIC_SB_CONNECTION = "connectedSB/" + IDUSER + "/true"
TOPIC_SB_DISCONNECTION = "disconnectedSB/" + IDUSER + "/true"
TOPIC_FD_PLAY_SOUND = "songPlayed/" + IDUSER
TOPIC_FD_WARNING = "notification/" + IDUSER + "/warning"
TOPIC_FD_PLAY_PAUSE = "playPlaylist/" + IDUSER
# songPlayed/64429949d35dee5ae5c96997

PLAY = 1
STOP = 0
PAUSE = 2

status_player = STOP
current_playlist = ""

# TOPIC_BUTTONS = "mqtt-buttonNumberClicked/" + IDUSER
# TOPIC_UPDATE_PAD = "mqtt-updateTable/" + IDUSER
# TOPIC_UPDATE_SOUNDS = "mqtt-updateSong/" + IDUSER
# MQTT_PATH = "test_channel_Pao" #this is the name of topic, like temp
URL_COMMUN = "https://presetmidi.herokuapp.com/api/"

playlist = dict()
random_bool = False
event = multiprocessing.Event()
queue = multiprocessing.Queue()

receiver, sender = multiprocessing.Pipe()

BOUTON1 = 17
BOUTON2 = 27
BOUTON3 = 22
BOUTON4 = 5
BOUTON5 = 6
BOUTON6 = 13

GPIO.setmode(GPIO.BCM)

GPIO.setup(BOUTON1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BOUTON2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BOUTON3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BOUTON4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BOUTON5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BOUTON6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

now = datetime.datetime.now()

file = open("/home/pi/SoundBox/logs.txt", "a")
file.write("\n\n\n\n\n----------------------" + str(now) + "----------------------")
file.write("\n")
file.close()

def is_cnx_active(timeout):
    """Cette fonction permet de détecter si la raspberry est connectée à l'internet"""

    try:
        requests.head("https://preset.herokuapp.com/", timeout=timeout)
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

def update_sounds(client):
    """Cette fonction permet de télécharger un son s'il est ajouté sur la bibliothèque en ligne
    de l'utilisateur. Il supprime également les sons existant sur la raspberry et pas en ligne"""

    wait_for_connection()
    print("update sound")
    if client is not None:
        client.publish(TOPIC_FD_WARNING, "Preset se synchronise")
    # Fetch all sound ids
    url = URL_COMMUN + "songBoard/getSongBoard/" + IDUSER

    response = requests.get(url)
    if response.status_code != 200:
        print ("Error:", response.status_code)
    else:
        print ("Status 200")
    # print(response.text)

    rep_json = response.json()
    for button_id, details in rep_json.items():
        # print(button_id)
        dir_list = os.listdir("/home/pi/sounds/" + button_id)
        online = list()

        for detail_name, detail in details.items():
            if detail_name == "songs":
                for song in detail:
                    if song is not None:
                        for metadata, value in song.items():
                            # print(metadata + ": " + value)
                            if metadata == "_id":
                                online.append(value)
                                if value not in dir_list:
                                    print("downloading sound " + song["_id"] + " " + song["audioName"])
                                    download_sound(song["_id"], button_id)

        for song_local in dir_list:
            if song_local not in online:
                print("removing sound " + song_local)
                os.remove("/home/pi/sounds/" + button_id + '/' + song_local)
        
        playlist[button_id] = online
    
    for key, item in playlist.items():
        print(key)
        print(item)


def download_sound(id_sound, button):
    # Download the corresponding sound
    url = URL_COMMUN + "audios/byId/" + id_sound + '/' + IDUSER
    response = requests.get(url)
    if response.status_code != 200:
        print ("Error:", response.status_code)

    data = response.json()
    print(data)
    b = base64.b64decode(data[0]["datas"])
    # print(b)

    songFile = "/home/pi/sounds/" + button + "/" + id_sound
    print(songFile)
    # input("wait")
    with open(songFile, 'wb') as output_file:
        output_file.write(b)



def run_playlist(button, receiver):
    playlist_sort = playlist[button]
    if random_bool:
        random.shuffle(playlist_sort)

    for song in playlist_sort:
        receiver.send(song)
        # client.publish(TOPIC_FD_PLAY_SOUND, song)
        # client.publish("test", "hello")

        file = open("/home/pi/SoundBox/logs.txt", "a")
        file.write("\n### in run_playlist() ###\n")
        command = "mpg123 /home/pi/sounds/" + button + '/' + song
        song_path = "/home/pi/sounds/" + button + '/' + song
        command_try = "LOAD " + song_path + "\n"
        print(command_try)
        print("command: " + command)
        file.write("\tcommand: " + command + "\n")
        file.close()
        # os.system(command)
        process = subprocess.Popen(["/usr/bin/mpg123", "-R", song_path], stdout=None, stdin=subprocess.PIPE, stderr=None)
        # time.sleep(1.0)
        process.stdin.write(bytes(command_try, 'utf-8'))
        process.stdin.flush()
        # process = subprocess.Popen(["/usr/bin/mpg123", song_path], stdin=master)
        # process = subprocess.run(command, capture_output=True, text=True)
        i = 0
        while process.poll() is None:
            i += 1
            if i == 100000:
                file = open("/home/pi/SoundBox/logs.txt", "a")
                file.write("\n### in run_playlist() ###\n\tplaying\n")
                file.close()
                print("running2")
                i = 0
            # print("hello")
            if event.is_set():
                print("terminating process")
                process.terminate()
                break
            # if not queue.empty():
            #     comm = queue.get()
            #     if comm is not None:
            #         # if item == "pause":
            #         print("sending s")
            #         os.write(slave, b's')
            #         # process.communicate(input = b's')
            if receiver.poll():
                comm = receiver.recv()
                if comm is not None:
                    # if item == "pause":
                    file = open("/home/pi/SoundBox/logs.txt", "a")
                    file.write("\n### in run_playlist() ###\n\tsending s")
                    file.close()
                    print("sending s")
                    process.stdin.write(b"PAUSE\n")
                    process.stdin.flush()
                    # process.stdin.flush()
                    # process.stdin.write(b"s\n")
                    # process.stdin.flush()
                    # os.write(slave, b's')
                    # process.communicate(input = b's')
        if event.is_set():
            break
        # os.system(command)


def play_button(button, client):
    """Cette fonction joue la musique attribué au bouton cliqué"""
    global receiver
    file = open("/home/pi/SoundBox/logs.txt", "a")
    file.write("\n\t --- playing_button ---")
    file.close()
    process = multiprocessing.Process(target=run_playlist, kwargs={"button":button, "receiver":receiver})
    process.start()
    status_player = PLAY
    print("process started")
    # for song in playlist[button]:
    #     command = "mpg123 /home/pi/sounds/" + button + '/' + song
    #     song_path = "/home/pi/sounds/" + button + '/' + song
    #     print("command: " + command)
    #     # os.system(command)
    #     process = subprocess.Popen(["/usr/bin/mpg123", song_path])
    # dir_list = os.listdir("/home/pi/sounds/" + button)
    # for song in playlist[button]:
    #     command = "mpg123 /home/pi/sounds/" + button + '/' + song
    #     input(command)
    #     result = subprocess.run(command, capture_output=True, text=True)
    #     # os.system(command)

    # with open('/home/pi/SoundBox/soundPad.txt', 'r') as f:
    #     lines = f.read()
    # attribution = json.loads(lines)
    # cmd = "(cd /home/pi/SoundBox/soundManagement/ && ./a.out " + attribution[button[2:len(button)-1]] + " 0)"
    # print(cmd)
    # os.system(cmd)


def update_pad():
    """Cette fonction met à jour la table d'attribution (pad)"""

    wait_for_connection()
    url = URL_COMMUN + "songPad/getAll/" + IDUSER
    response = requests.get(url)
    if response.status_code != 200:
        print ("Error:", response.status_code)
    rep_text = response.text
    with open('/home/pi/SoundBox/soundPad.txt', 'w') as f:
        f.write(rep_text)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    """Callback appelé à la connection de la raspberry sur le serveur MQTT"""

    print("Connected with result code "+str(rc))
 
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe(TOPIC_BUTTONS)
    # client.subscribe(TOPIC_UPDATE_PAD)
    # client.subscribe(TOPIC_UPDATE_SOUNDS)

    client.subscribe(TOPIC_PLAYLIST)
    client.subscribe(TOPIC_PLAYLIST_DEL)
    client.subscribe(TOPIC_SOUND_P)
    client.subscribe(TOPIC_SOUND_DEL)
    client.subscribe(TOPIC_RANDOM_P)
    client.subscribe(TOPIC_PLAY)
    client.subscribe(TOPIC_SITE_CONNECTION)

    client.publish(TOPIC_SB_CONNECTION, "ok")
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    """Callback appelé lorsqu'un message est reçu sur un topic"""
    global status_player
    global current_playlist
    global sender
    global random_bool

    print(msg.topic+" "+str(msg.payload))
    # client.publish(TOPIC_FD_PLAY_PAUSE, "test")

    file = open("/home/pi/SoundBox/logs.txt", "a")
    file.write("\n\n\n---- MQTT - Received message ---\n\t" + msg.topic+" "+str(msg.payload))
    file.close()

    if msg.topic == TOPIC_RANDOM_P:
        if str(msg.payload).find("true") != -1:
            random_bool = True
        elif str(msg.payload).find("false") != -1:
            random_bool = False

    elif msg.topic == TOPIC_PLAYLIST or msg.topic == TOPIC_PLAYLIST_DEL or msg.topic == TOPIC_SOUND_P or msg.topic == TOPIC_SOUND_DEL:
        update_sounds(client)

    elif msg.topic == TOPIC_PLAY:
        if str(msg.payload).find("true") != -1:
            playlist_msg = str(msg.payload)[str(msg.payload).find('\'')+1:str(msg.payload).find('/')]
            print("status_player: " + str(status_player))
            print("current_playlist: " + current_playlist)
            print("playlist_msg: " + playlist_msg)
            file = open("/home/pi/SoundBox/logs.txt", "a")
            file.write("\n\t" + "status_player: " + str(status_player) + "\n\t" + "current_playlist: " + current_playlist + "\n\t" + "playlist_msg: " + playlist_msg)
            file.close()
            if current_playlist == playlist_msg:
                if status_player == STOP:
                    status_player = PLAY
                    client.publish(TOPIC_FD_PLAY_PAUSE, str(current_playlist) + '/true')
                    event.clear()
                    play_button("button" + str(int(playlist_msg)+1), client)
                    file = open("/home/pi/SoundBox/logs.txt", "a")
                    file.write("\n\t\t --- play_beg ---")
                    file.close()
                elif status_player == PAUSE:
                    status_player = PLAY
                    client.publish(TOPIC_FD_PLAY_PAUSE, str(current_playlist) + '/true')
                    sender.send("play")
                    file = open("/home/pi/SoundBox/logs.txt", "a")
                    file.write("\n\t\t --- play ---")
                    file.close()
                    # queue.put("play")

            else: 
                current_playlist = playlist_msg
                event.set()
                time.sleep(0.1)
                event.clear()
                status_player = PLAY
                client.publish(TOPIC_FD_PLAY_PAUSE, str(current_playlist) + '/true')
                play_button("button" + str(int(playlist_msg)+1), client)


        elif str(msg.payload).find("false") != -1:
            print("status_player: " + str(status_player))
            if status_player == PLAY:
                client.publish(TOPIC_FD_PLAY_PAUSE, str(current_playlist) + '/false')
                status_player = PAUSE
                file = open("/home/pi/SoundBox/logs.txt", "a")
                file.write("\n\t\t --- pausing ---")
                file.close()
                print("pausing")
                sender.send("pause")
                # queue.put("pause")
            # event.set()

    elif msg.topic == TOPIC_SITE_CONNECTION:
        client.publish(TOPIC_SB_CONNECTION, "ok")

    file = open("/home/pi/SoundBox/logs.txt", "a")
    file.write("\n")
    file.close()

engine.say("Connecting to network")
engine.runAndWait()
# if __name__ == '__main__':
update_sounds(None)
wait_for_connection()
client = mqtt.Client(transport='websockets')
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username=MQTT_USERNAME,password=MQTT_PASSWORD)
client.will_set(TOPIC_SB_DISCONNECTION, "ok")
client.connect(MQTT_SERVER, MQTT_PORT)
print(IDUSER)
# client.loop_forever() #use this line if you don't want to write any further code. It blocks the code forever to check for data
client.loop_start()  #use this line if you want to write any more code here
engine.say("Successfully connected")
engine.runAndWait()
while True:
    if sender.poll():
        comm = sender.recv()
        if comm is not None:
            client.publish(TOPIC_FD_PLAY_SOUND, comm)
    time.sleep(0.1)
    button_pressed = False
    button = ""
    while GPIO.input(BOUTON1) :
        time.sleep(0.1)
        print("pressed")
        button="0"
        button_pressed = True
    while GPIO.input(BOUTON2) :
        time.sleep(0.1)
        button="1"
        button_pressed = True
    while GPIO.input(BOUTON3) :
        time.sleep(0.1)
        button="2"
        button_pressed = True
    while GPIO.input(BOUTON4) :
        time.sleep(0.1)
        button="3"
        button_pressed = True
    while GPIO.input(BOUTON5) :
        time.sleep(0.1)
        button="4"
        button_pressed = True
    while GPIO.input(BOUTON6) :
        time.sleep(0.1)
        button="5"
        button_pressed = True

    if button_pressed:
        if current_playlist == button:
            if status_player == STOP:
                status_player = PLAY
                event.clear()
                play_button("button" + str(int(button)+1), client)

            elif status_player == PAUSE:
                status_player = PLAY
                sender.send("play")
                # queue.put("play")

            elif status_player == PLAY:
                status_player = PAUSE
                print("pausing")
                sender.send("pause")
                # queue.put("pause")
        
        else:
            current_playlist = button
            event.set()
            time.sleep(0.1)
            event.clear()
            status_player = PLAY
            play_button("button" + str(int(button)+1), client)