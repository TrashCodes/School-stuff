# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from gpiozero import MCP3008
import sys
import Adafruit_DHT
import telepot
import datetime as datetime
import json
from gpiozero import Buzzer
from picamera import PiCamera
from rpi_lcd import LCD
from PIL import Image
from multiprocessing import Process
import string, random
import time
# Setting up the pin for the dht sensor, the buzzer and LCD

adc = MCP3008(channel=0)
bz = Buzzer(5)
lcd = LCD()


host = "acway7h5aefsa-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "getEnvironmentCert/rootca.pem"
certificatePath = "getEnvironmentCert/certificate.pem.crt"
privateKeyPath = "getEnvironmentCert/private.pem.key"



global update
update = True


def rand_str_gen(size=20):
    lettersal = ''.join(random.choice(string.ascii_letters) for i in range(size))
    lettersd = ''.join(random.choice(string.digits) for i in range(size))
    lettersp = ''.join(random.choice(string.punctuation) for i in range(size))
    letter = str(lettersal) + str(lettersd) + str(lettersp)
    return ''.join(random.choice(letter) for i in range(size))

# Function to take a picture from PI camera                            
def takePic():
      timestring = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
      print ("Taking photo at " +timestring)
      with PiCamera() as camera:
        camera.capture('photo/photo_'+timestring+'.jpg') 
        print("photo/photo_"+timestring+".jpg")

        # As the image is taken upside down, we need to rotate it by 180 degree
        colorImage  = Image.open('photo/photo_'+timestring+'.jpg')
        transposed  = colorImage.transpose(Image.ROTATE_180)
        transposed.save('photo/photo_'+timestring+'.jpg')
        
        # Send a telegram msg and the photo taken to the user 
        send_user_Msg("This is what the user is doing :)")
        send_photo(timestring)

# Turn on the buzzer
def buzzerOn():
      for x in range(3):
            bz.beep()
            sleep(0.3)
            bz.off()
            sleep(0.3)

# Function to send the user a telegram msg
def send_user_Msg(data):
      bot_token = '919519674:AAGLInv0JSMvhaTuTz-itTFcNcvuSSIWnM4'
      bot = telepot.Bot(bot_token)
      chat_id = '277560176'
      bot.sendMessage(chat_id, data)

# Function to send the user a telegram photo
def send_photo(data):
      bot_token = '919519674:AAGLInv0JSMvhaTuTz-itTFcNcvuSSIWnM4'
      bot = telepot.Bot(bot_token)
      chat_id = '277560176'
      bot.sendPhoto(chat_id, photo=open("photo/photo_" + data+'.jpg', 'rb'))


# while loop to listen to mqtt for taking pic
def subscribeTakePicMqtt():
      global update 
      my_rpi = AWSIoTMQTTClient("PubSub-p1726819" + rand_str_gen())
      my_rpi.configureEndpoint(host, 8883)
      my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

      my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
      my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
      my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
      my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

      # Connect and subscribe to AWS IoT
      my_rpi.connect()
      my_rpi.subscribe("sensor/takePic", 1, customCallback)

      while True:
            print("Waiting for call...")
            sleep(5)
            


def customCallback(client, userdata, message):
      payload = json.loads(message.payload)
      if payload["deviceID"] == "CA2":
            lcd = LCD()
            lcd.clear()
            takePic()
            lcd.text('Time to eat', 1)
            lcd.text('medicine', 2)
            buzzerOn()
            lcd.clear()

            


if __name__ == '__main__':
    subscribe_proc = Process(name='subscribeTakePicMqtt',target=subscribeTakePicMqtt)
    subscribe_proc.start()
    subscribe_proc.join()
