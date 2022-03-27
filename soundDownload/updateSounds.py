import requests
import json
import base64

url="https://preset-midi-player.herokuapp.com/api/audios/byName/"
url += "piste5.mp3/"
url += "623f9e6506e7e4278e1927d7"

r = requests.get(url)

if r.status_code != 200:
    print ("Error:", r.status_code)
data = r.json()
b = base64.b64decode(data[0]["datas"])
print(b)

with open('/home/pi/sounds/piste5.mp3', 'wb') as output_file:
  output_file.write(b)

#print(data)