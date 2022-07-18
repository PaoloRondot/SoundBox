import requests
import json
import base64

url="https://preset-midi-player.herokuapp.com/api/audios/byName/"
url += "ventouse/"
url += "61c356d1670d8027c6e8a818"

r = requests.get(url)

if r.status_code != 200:
    print ("Error:", r.status_code)

data = r.json()
print(data)
b = base64.b64decode(data[0]["datas"])
print(b)

with open('/home/pi/sounds/ventouse.mp3', 'wb') as output_file:
  output_file.write(b)

#print(data)