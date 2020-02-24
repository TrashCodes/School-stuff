# Import neccessary library 
from flask import Flask, render_template, jsonify, request,Response
import sys
import json
import numpy
import datetime
import decimal
import telepot
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer
import time
from time import sleep
from decimal import Decimal
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


gevent.monkey.patch_all()

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

        # Return the data obtained
        return data_reversed

    except:
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])

# Converting data to json
class GenericEncoder(json.JSONEncoder):
    
    def default(self, obj):  
        if isinstance(obj, numpy.generic):
            return numpy.asscalar(obj)
        elif isinstance(obj, Decimal):
            return str(obj) 
        elif isinstance(obj, datetime.datetime):  
            return obj.strftime('%Y-%m-%d %H:%M:%S') 
        elif isinstance(obj, Decimal):
            return float(obj)
        else:  
            return json.JSONEncoder.default(self, obj) 

def data_to_json(data):
    json_data = json.dumps(data,cls=GenericEncoder)
    return json_data


app = Flask(__name__)

# Get the last 10 records of the temperature and humidity from the database
@app.route("/api/getHumidityTempData",methods = ['POST', 'GET'])
def apidata_getdata():
    if request.method == 'POST':
        try:    
            number = 10
            data = {'chart_data': data_to_json(get_data_from_dynamodb(number,'Humidity_Temp',-1)), 'title': "IOT Data"}
            return jsonify(data)
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])

# Get real time data from the DHT11 sensor 
@app.route("/api/getRealTimeData",methods = ['POST', 'GET'])
def apidata_getRealTime():
    if request.method == 'POST':
        try:
            number = 1  
            data = {'chart_data': data_to_json(get_data_from_dynamodb(number,'Humidity_Temp',-1)), 'title': "IOT Data"}
            return jsonify(data)     
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])

# Take the last 10 records of the take medicine history from the database
@app.route("/api/eatMed",methods = ['POST', 'GET'])
def apidata_eatMed():
        try:   
            number = 10  
            data = {'chart_data': data_to_json(get_data_from_dynamodb(number,'takeMed',1)), 'title': "IOT Data"}
            return jsonify(data)  
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])

# Take the last 10 records of the take medicine history from the database
@app.route("/api/eatLiquidMed",methods = ['POST', 'GET'])
def apidata_eatLiquidMed():
        try:   
            number = 10  
            data = {'chart_data': data_to_json(get_data_from_dynamodb(number,'takeMedLiquid',1)), 'title': "IOT Data"}
            return jsonify(data)  
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])

# Get real time data from the PH value 
@app.route("/api/getRealTimePHValue",methods = ['POST', 'GET'])
def getRealTimePHValue():
    if request.method == 'POST':
        try:
            number = 1  
            data = {'chart_data': data_to_json(get_data_from_dynamodb(number,'PHValue',-1)), 'title': "IOT Data"}
            return jsonify(data)     
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])

# Take the last 10 records Ph value from the database
@app.route("/api/getPHValueData",methods = ['POST', 'GET'])
def getPHValueData():
        try:   
            number = 10  
            data = {'chart_data': data_to_json(get_data_from_dynamodb(number,'PHValue',1)), 'title': "IOT Data"}
            return jsonify(data)  
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])


# Reminder function to take pic and alert user
@app.route("/api/takePhoto")
def takePhoto():

    # Modifying the message header and data
    message = {}
    message["deviceID"] = "CA2"
    now = datetime.datetime.now()
    message["datetimeID"] = now.isoformat()   
    my_rpi.publish("sensor/takePic", json.dumps(message), 1)
    sleep(2)   
    response= 'Done! :)'
    return response

# To upload the new pill schedule to DB
@app.route('/api/updatePillSchedule', methods=['GET','POST'])      
def publishMqttPill():
    value = request.args.get('value')
    print(value)
    # Modifying the message header and data
    message = {}
    message["deviceID"] = "CA2"
    now = datetime.datetime.now()
    message["datetimeID"] = now.isoformat()
    message["schedule"] = value
    my_rpi.publish("sensor/pillSchedule", json.dumps(message), 1)
    return message

# To upload new liquid scheduke to DB
@app.route('/api/updateLiquidSchedule', methods=['GET','POST'])      
def publishMqttLiquid():
    value = request.args.get('value')
    print(value)
    # Modifying the message header and data
    message = {}
    message["deviceID"] = "CA2"
    now = datetime.datetime.now()
    message["datetimeID"] = now.isoformat()
    message["schedule"] = value
    my_rpi.publish("sensor/liquidSchedule", json.dumps(message), 1)
    return message


@app.route("/")
def chartsimple():
    return render_template('index.html')

if __name__ == '__main__':
   try:
        print('Server waiting for requests')
        http_server = WSGIServer(('0.0.0.0', 8001), app)
        app.debug = True
        http_server.serve_forever()
   except:
        print("Exception")
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])


