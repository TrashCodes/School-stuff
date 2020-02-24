import serial
import RPi.GPIO as GPIO
import mysql.connector
import json
import telepot
import sys
from time import sleep
import datetime as datetime
import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr
from twilio.rest import Client
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import threading
from multiprocessing import Process
import string, random

def rand_str_gen(size=20):
    lettersal = ''.join(random.choice(string.ascii_letters) for i in range(size))
    lettersd = ''.join(random.choice(string.digits) for i in range(size))
    lettersp = ''.join(random.choice(string.punctuation) for i in range(size))
    letter = str(lettersal) + str(lettersd) + str(lettersp)
    return ''.join(random.choice(letter) for i in range(size))

def get_data_from_dynamodb(number,database,number2):
    try:
        # Setting up the database name
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(database)

        # Getting today's date and format it to use as filter
        today = datetime.date.today()
        startdate = today.strftime("%Y-%m")

        # Getting data with filter
        response = table.query(
            KeyConditionExpression=Key('deviceID').eq('CA2')
                                  & Key('datetimeID').begins_with(startdate),
            ScanIndexForward=False,Limit=number
        )
        # Limit the data to last <number> of items
        items = response['Items']
        data = items[:number]
        data_reversed = data[::number2]
        dataString  = json.dumps(data_reversed)
        dataString = dataString[-11:-3]
        # Return the data obtained
        return dataString

    except:
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])


def send_user_Msg(data):
	bot_token = '919519674:AAGLInv0JSMvhaTuTz-itTFcNcvuSSIWnM4'
	bot = telepot.Bot(bot_token)
	chat_id = '277560176'
	bot.sendMessage(chat_id, data)

def getlivedata():
    return waterlevelchecker
    
def syrupSchedule():
    try:
        # To setup the certificate etc for mqtt
        host = "acway7h5aefsa-ats.iot.us-east-1.amazonaws.com"
        rootCAPath = "getEnvironmentCert/rootca.pem"
        certificatePath = "getEnvironmentCert/certificate.pem.crt"
        privateKeyPath = "getEnvironmentCert/private.pem.key"

        my_rpi2 = AWSIoTMQTTClient("PubSub-p1726819"  + rand_str_gen())
        my_rpi2.configureEndpoint(host, 8883)
        my_rpi2.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
        my_rpi2.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        my_rpi2.configureDrainingFrequency(2)  # Draining: 2 Hz
        my_rpi2.configureConnectDisconnectTimeout(10)  # 10 sec
        my_rpi2.configureMQTTOperationTimeout(5)  # 5 sec

	    # Connect and subscribe to AWS IoT
        my_rpi2.connect()
        update = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.OUT)
        
        while update:
            try:
                global medicine_time2
                global medicine_time2_plus
                data = get_data_from_dynamodb(1,'liquidSchedule',-1)
                medicine_time2 = data

                medicine_time2_plus = datetime.datetime.strptime(medicine_time2,"%H:%M:%S")
                medicine_time2_plus += datetime.timedelta(0,60)
                medicine_time2_plus = medicine_time2_plus.strftime("%H:%M:%S")

				# Get the current time now and check if it is the time specified
                now = datetime.datetime.now()
                time_string = now.strftime("%H:%M:%S")
                #medicine_time2_plus > time_string > medicine_time2
                if (1==1):
                    if (phlevelchecker <= 5.5 or phlevelchecker >= 8.5):
                        print("Unhealthy pH range of medicine, not safe for consumption. Alerting the user...")
                        send_user_Msg("pH value of medicine: " + str(phlevelchecker) + "UNSAFE FOR CONSUMPTION. DO NOT CONSUME. REPLACE IMMEDIATELY")
                    else:
                        print("Dispensing necessary amount of medicine into cup...")
                        #Standard 10-20ml dosage. Water level is in percentage. Assume that the cup the user drinks from is a small cup
                        #10-20ml of that cup would probably be around 15% of the cup
                        while waterlevelchecker < 15 :
                            print("Current amount of syrup poured into cup (%):\t"+str(waterlevelchecker))
                            GPIO.output(26, 0)
                            sleep(1)
                            GPIO.output(26, 1)
                            x = waterlevelchecker
                        print("Syrup dispensed")
                        print("Checking if the user drank the medicine")
                        sleep(10)
                        if(waterlevelchecker > 5):
                            #never drink
                            print("User did not drink. Sending a message...")
                            # Send a msg to the user telling that the patient did not take medicine on time
                            send_user_Msg("User did not eat medicine on time")
                            new_now = datetime.datetime.now()
                            # Get the current date and time and insert into the database
                            False_string = 'False'
                            message = {}
                            message["deviceID"] = "CA2"
                            message["datetimeID"] = new_now.isoformat()
                            message["takenOnTime"] = False_string
                            my_rpi2.publish("sensor/takeMedLiquid", json.dumps(message), 1)
                            
                            sleep(60)
                        else:
                            print("User drank the medicine")
                            new_now = datetime.datetime.now()
                            True_string = 'True'
                            message = {}
                            message["deviceID"] = "CA2"
                            message["datetimeID"] = new_now.isoformat()
                            message["takenOnTime"] = True_string
                            my_rpi2.publish("sensor/takeMedLiquid", json.dumps(message), 1)
                            
                            sleep(60)
            except KeyboardInterrupt:
                update = False
                cursor.close()
                cnx.close()
            except:
                print("Error while inserting data...")
                print(sys.exc_info()[0])
                print(sys.exc_info()[1])
    except:
        print("FINAL")
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])


def reading():
    try:
        host = "acway7h5aefsa-ats.iot.us-east-1.amazonaws.com"
        rootCAPath = "getEnvironmentCert/rootca.pem"
        certificatePath = "getEnvironmentCert/certificate.pem.crt"
        privateKeyPath = "getEnvironmentCert/private.pem.key"

        my_rpi = AWSIoTMQTTClient("PubSub-p1726851" + rand_str_gen())
        my_rpi.configureEndpoint(host, 8883)
        my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

        my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
        my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
        my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect and subscribe to AWS IoT
        my_rpi.connect()
        ser = serial.Serial('/dev/ttyUSB0',19200)
        print(ser.name)

        buf = ""
        a=0
        ser.flush()
        
        while True:
            #constantly read
            buf = ser.read()
            sleep(0.1)
            data_left=ser.inWaiting()
            buf += ser.read(data_left)

            #filtering retrieved data
            if "waterlevel\n" in  buf:
                waterlevel = buf.strip("waterlevel\n")
                #print(waterlevel)
                global waterlevelchecker
                waterlevelchecker = float(waterlevel)
                buf = ""
                ser.flush()
            elif "ph\n" in buf:
                phlevel = buf.strip("ph\n")
                #print(phlevel)
                global phlevelchecker
                phlevelchecker = float(phlevel)
                buf = ""
                message = {}
                message["deviceID"] = "CA2"
                now = datetime.datetime.now()
                message["datetimeID"] = now.isoformat()
                message["phVal"] = phlevel
                my_rpi.publish("sensor/PHValue", json.dumps(message), 1)
                ser.flush()
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])



if __name__ == '__main__':
    waterlevelchecker = 0
    global phlevelchecker
    global medicine_time2
    global medicine_time2_plus

    thread1 = threading.Thread(target=syrupSchedule)
    thread2 = threading.Thread(target=reading)
    thread1.start()
    thread2.start()

