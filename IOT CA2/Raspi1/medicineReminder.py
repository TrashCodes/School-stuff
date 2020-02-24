
global medicine_time 
global medicine_time2


# Import neccessary library 
import datetime
from gpiozero import MCP3008
from time import sleep
import sys
from rpi_lcd import LCD
from gpiozero import MotionSensor,Buzzer
from picamera import PiCamera
import telepot
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr
import threading
from multiprocessing import Process
import string, random

def rand_str_gen(size=20):
    lettersal = ''.join(random.choice(string.ascii_letters) for i in range(size))
    lettersd = ''.join(random.choice(string.digits) for i in range(size))
    lettersp = ''.join(random.choice(string.punctuation) for i in range(size))
    letter = str(lettersal) + str(lettersd) + str(lettersp)
    return ''.join(random.choice(letter) for i in range(size))

def takePhoto(file_path,file_name):
    with PiCamera() as camera:
        #camera.resolution = (1024, 768)
        full_path = file_path + "/" + file_name
        camera.capture(full_path)
        sleep(3)

def uploadToS3(file_path,file_name, bucket_name,location):
    s3 = boto3.resource('s3') # Create an S3 resource
    exists = True

    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False

    if exists == False:
        s3.create_bucket(Bucket=bucket_name,CreateBucketConfiguration=location)
    
    # Upload the file
    full_path = file_path + "/" + file_name
    s3.Object(bucket_name, file_name).put(Body=open(full_path, 'rb'))
    print("File uploaded")


def detect_faces(bucket, key, max_labels=10, min_confidence=90, region="us-east-1"):
    rekognition = boto3.client("rekognition", region)
    response = rekognition.detect_faces(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        Attributes=['ALL']
    )
    return response['FaceDetails']


# Function to send user telegram msg
def send_user_Msg(data):
	bot_token = '919519674:AAGLInv0JSMvhaTuTz-itTFcNcvuSSIWnM4'
	bot = telepot.Bot(bot_token)
	chat_id = '277560176'
	bot.sendMessage(chat_id, data)


# Function to retrieve data where the data is base on the database and the number of row depends on variable number
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
        data_reversed = data[::number2]
        dataString  = json.dumps(data_reversed)
        dataString = dataString[-11:-3]

        # Return the data obtained
        return dataString

    except:
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])


# While loop to check if schedule reached
def pillSchedule():
	try:

		# Setting up the pin for the dht sensor, the buzzer and motion sensor
		pin = 4
		bz = Buzzer(5)
		pir = MotionSensor(26, sample_rate=20,queue_len=1)

		# To setup the certificate etc for mqtt
		host = "acway7h5aefsa-ats.iot.us-east-1.amazonaws.com"
		rootCAPath = "getEnvironmentCert/rootca.pem"
		certificatePath = "getEnvironmentCert/certificate.pem.crt"
		privateKeyPath = "getEnvironmentCert/private.pem.key"



		# Set the filename and bucket name
		BUCKET = 'sp-p1726819-s3-bucket' 
		location = {'LocationConstraint': 'us-east-1'}
		file_path = "/home/pi/labs/assignment/photo"
		file_name = "user.jpg"

		my_rpi = AWSIoTMQTTClient("PubSub-p1726819"  + rand_str_gen())
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
			try:
				global medicine_time
				data = get_data_from_dynamodb(1,'pillSchedule',-1)
				medicine_time = data
				global medicine_time_plus
				medicine_time_plus = datetime.datetime.strptime(medicine_time,"%H:%M:%S")
				medicine_time_plus += datetime.timedelta(0,60)
				medicine_time_plus = medicine_time_plus.strftime("%H:%M:%S")


				# Get the current time now and check if it is the time specified
				now = datetime.datetime.now()
				time_string = now.strftime("%H:%M:%S")
				if (medicine_time_plus> time_string > medicine_time):
					
					# Alert the user by turning on the buzzer
					bz.on()
					print("Time to eat medicine")
					
					# Print on the LCD to tell the user to take med
					lcd = LCD()
					lcd.text('Time to eat', 1)
					lcd.text('medicine :)', 2)
					
					# Checking how long did the user take to take the medicine after buzzer on
					old_now = datetime.datetime.now().strftime("%H:%M:%S")
					start_dt = datetime.datetime.strptime(old_now, '%H:%M:%S')
					pir.wait_for_motion(10) # Motion sensor will only wait for 10 seconds
					new_now = datetime.datetime.now()
					new_time = new_now.strftime("%H:%M:%S")
					end_dt = datetime.datetime.strptime(new_time, '%H:%M:%S')
					duration = (end_dt - start_dt) 
					diff = int(duration.seconds)	
					
					# If the user took more than 10 seconds it means that the user did not take the medicine on time 
					
					if diff < 8:
						
						# Take a photo and store to S3 
						takePhoto(file_path, file_name)
						uploadToS3(file_path,file_name, BUCKET,location)

						ageLow = 0
						ageHigh = 0

						# Print the deteced face attribute 
						print('Detected faces for')    
						for faceDetail in detect_faces(BUCKET, file_name):
						    ageLow = faceDetail['AgeRange']['Low']
						    ageHigh = faceDetail['AgeRange']['High']
						    print('Age between {} and {} years old'.format(ageLow,ageHigh))
						    print('Here are the other attributes:')
						    print(json.dumps(faceDetail, indent=4, sort_keys=True))

						# To ensure that the medicine is taken by elderly and not others (Kids or pets)
						if (ageLow < 20 < ageHigh):

							# The medicine is taken in less than 10 seconds, turn off buzzer
							lcd.text('Medicine taken', 1)
							lcd.text('successfully :)', 2)
							print("User ate medicine after {:.2f} seconds".format(diff))
							bz.off()
							
							# Get the current date and time and insert the data into the database
							True_string = 'True'
							message = {}
							message["deviceID"] = "CA2"
							message["datetimeID"] = new_now.isoformat()      
							message["takenOnTime"] = True_string
							my_rpi.publish("sensor/takeMed", json.dumps(message), 1)
							
							# Clear LCD 
							print("Uploaded data to database")
							print("Waiting for next schedule")
							lcd.clear()
							sleep(60)

						# The medicine is not taken by elderly 
						else: 	
							bz.off()
							print("Medicine not taken by patient")
							
							# Send a msg to the user telling that the patient did not take medicine on time
							send_user_Msg("Medicine not taken by patient")
							
							# Get the current date and time and insert into the database
							False_string = 'False'
							message = {}
							message["deviceID"] = "CA2"
							message["datetimeID"] = new_now.isoformat()      
							message["takenOnTime"] = False_string
							my_rpi.publish("sensor/takeMed", json.dumps(message), 1)
							
							# Clear LCD
							print("Uploaded data to database")
							print("Waiting for next schedule")
							lcd.clear()
							sleep(60)

							
					else:
						# The user did not take medicine within 10 seconds 
						bz.off()
						print("Patient did not take medicine on time")
						
						# Send a msg to the user telling that the patient did not take medicine on time
						send_user_Msg("User did not eat medicine on time")
						
						# Get the current date and time and insert into the database
						False_string = 'False'
						message = {}
						message["deviceID"] = "CA2"
						message["datetimeID"] = new_now.isoformat()      
						message["takenOnTime"] = False_string
						my_rpi.publish("sensor/takeMed", json.dumps(message), 1)
						
						# Clear LCD
						print("Uploaded data to database")
						print("Waiting for next schedule")
						lcd.clear()
						sleep(60)

			except KeyboardInterrupt:
			 	update = False
			except:
			 	print("Error while inserting data...")
				print(sys.exc_info()[0])
				print(sys.exc_info()[1])
	except:
		print(sys.exc_info()[0])
		print(sys.exc_info()[1])





if __name__ == '__main__':
    subscribe_proc = Process(name='pillSchedule', target=pillSchedule)
    subscribe_proc.start()
    subscribe_proc.join()
