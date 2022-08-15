import RPi.GPIO as GPIO
import json
import os


BOUTON1 = 17
BOUTON2 = 27
BOUTON3 = 22
BOUTON4 = 5
BOUTON5 = 6
BOUTON6 = 13

GPIO.setmode(GPIO.BCM)

GPIO.setup(BOUTON1, GPIO.IN)
GPIO.setup(BOUTON2, GPIO.IN)
GPIO.setup(BOUTON3, GPIO.IN)
GPIO.setup(BOUTON4, GPIO.IN)
GPIO.setup(BOUTON5, GPIO.IN)
GPIO.setup(BOUTON6, GPIO.IN)

def play_sound(bouton):
    with open('/home/pi/soundbox/soundPad.txt', 'r') as f:
        lines = f.read()
    attribution = json.loads(lines)
    cmd = "(cd /home/pi/soundbox/soundManagement/ && ./a.out " + attribution[bouton] + " 0)"
    print(cmd)
    os.system(cmd)

while True:
    if GPIO.input(BOUTON1) :
        play_sound("button1")
    elif GPIO.input(BOUTON2) :
        play_sound("button2")
    elif GPIO.input(BOUTON3) :
        play_sound("button3")
    elif GPIO.input(BOUTON4) :
        play_sound("button4")
    elif GPIO.input(BOUTON5) :
        play_sound("button5")
    elif GPIO.input(BOUTON6) :
        play_sound("button6")