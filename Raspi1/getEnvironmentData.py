# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from gpiozero import MCP3008
import sys
import Adafruit_DHT
import datetime as datetime
import json
from gpiozero import Buzzer
from picamera import PiCamera
from rpi_lcd import LCD
from PIL import Image
import threading

# Setting up the pin for the dht sensor, the buzzer and LCD

adc = MCP3008(channel=0)
pin = 4
bz = Buzzer(5)
camera = PiCamera()
lcd = LCD()


host = "acway7h5aefsa-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "getEnvironmentCert/rootca.pem"
certificatePath = "getEnvironmentCert/certificate.pem.crt"
privateKeyPath = "getEnvironmentCert/private.pem.key"

my_rpi = AWSIoTMQTTClient("PubSub-p1726819")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()


update = True


while update:
    # Get the humidity and temperture fromm the DHT11 sensor
    humidity, temperature = Adafruit_DHT.read_retry(11, pin)
    
    # Modifying the message header and data
    message = {}
    message["deviceID"] = "CA2"
    now = datetime.datetime.now()
    message["datetimeID"] = now.isoformat()      
    message["value"] = humidity
    message["value2"] = temperature
    my_rpi.publish("sensor/environment", json.dumps(message), 1)
    print(message)
    sleep(2)   