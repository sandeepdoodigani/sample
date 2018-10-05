import RPi.GPIO as GPIO
import dht11
import time
import sys
import ibmiotf.application
import ibmiotf.device
import random
import demjson
import json
from os.path import join,dirname
from os import environ
from watson_developer_cloud import VisualRecognitionV3
from pprint import pprint
import picamera
import swiftclient

cnt= 0

#Provide your IBM Watson Device Credentials
organization = "8l7a6i"
deviceType = "mydevice"
deviceId = "device"
authMethod = "token"
authToken = "RXwI61!iv5RCqbwX3?"

auth_url ="https://identity.open.softlayer.com/v3"
password="I_0sWd.I_64_.z3]"
project_id="cc0fc1aa37c147d58e3099484c72b41e"
user_id="eaff2b4c4d994c79802792f14f0e53f3"
region_name="dallas"
conn = swiftclient.Connection(key=password, 
	authurl=auth_url,  
	auth_version='3', 
	os_options={"project_id": project_id, 
				"user_id": user_id, 
				"region_name": region_name})
visual_recognition = VisualRecognitionV3(VisualRecognitionV3.latest_version, api_key='59cbed082bf9be2ce58603356aba10b1b0616c05')

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setup(16,GPIO.OUT)
GPIO.setup(20,GPIO.OUT)
GPIO.setup(21,GPIO.OUT)

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.IN)
GPIO.setup(15, GPIO.IN)
val=0


# read data using pin 12
SensorInstance = dht11.DHT11(pin = 15)


# Initialize the device client.
try:
	deviceOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
	deviceCli = ibmiotf.device.Client(deviceOptions)
except Exception as e:
	print("Caught exception connecting device: %s" % str(e))
	sys.exit()

def mycommandCallback(cmd):
                print ("command received: %s "  % cmd.data['payload'])
                s=str(cmd.data['payload'])
                print s
                if(s=="LIGHTON"):
                        GPIO.output(16,True)
                elif(s=="LIGHTOFF"):
                        GPIO.output(16,False)
                elif(s=="FANON"):
                        GPIO.output(20,True)
                elif(s=="FANOFF"):
                        GPIO.output(20,False)
                elif(s=="PUMPON"):
                        GPIO.output(21,True)
                elif(s=="PUMPOFF"):
                        GPIO.output(21,False)

def cameras(cmd):
        global cnt
        print "Camera"
        camera = picamera.PiCamera()
        file_path = '/home/pi/Desktop/our project/images/'+str(cnt)+'.jpg'
        camera.capture(file_path)
        camera.close()
        
            
        with open(join(dirname(__file__), file_path), 'rb') as image_file:
                response = visual_recognition.classify(images_file=image_file, threshold=0, classifier_ids=['face_459320211']);
                pprint(response)
                print(response['images'][0]['classifiers'][0]['classes'][1]['score'])
                
                if(response['images'][0]['classifiers'][0]['classes'][1]['score']>0.9):
                        print("Sandeep")
                         
                cont_name = "mycontainer"
                conn.put_container(cont_name)
                file_name = 'images/'+str(cnt)+'.jpg'
        with open(file_name, 'rb') as upload_file:
                conn.put_object(cont_name, file_name, contents= upload_file.read())

                
        cnt=cnt+1        


# Connect and send a datapoint "hello" with value "world" into the cloud as an event of type "greeting" 10 times
deviceCli.connect()
while True:
        #Get Sensor Data from DHT11
        SensorData = SensorInstance.read()
        val = GPIO.input(14)
        print val
        if(val==0):
                cameras("")
                if SensorData.is_valid():
                        T = SensorData.temperature
                        H = SensorData.humidity
                        data = { 'Temperature' : T, 'Humidity': H ,'door':val,'file_name':'images/'+str(cnt)+'.jpg'}
                        #print data
                        def myOnPublishCallback():
                            print "Published Temperature = %s C" % T, "Humidity = %s %%" % H, "to IBM Watson"
                        success = deviceCli.publishEvent("DHT11", "json", data, qos=0, on_publish=myOnPublishCallback)
                        if not success:
                                print("Not connected to IoTF")
                        time.sleep(2)

                else:
                        print "SensorData Invalid"
        
                deviceCli.commandCallback=mycommandCallback
        else :
                print "No one at door"
                time.sleep(1)
                if SensorData.is_valid():
                #if True:
                    T = SensorData.temperature
                    H = SensorData.humidity
                    data = { 'Temperature' : T, 'Humidity': H ,'door':val}
                    #print data
                    def myOnPublishCallback():
                            print "Published Temperature = %s C" % T, "Humidity = %s %%" % H, "to IBM Watson"
                    success = deviceCli.publishEvent("DHT11", "json", data, qos=0, on_publish=myOnPublishCallback)
                    if not success:
                            print("Not connected to IoTF")
                    time.sleep(2)

                else:
                    print "SensorData Invalid"
                #Send Temperature & Humidity to IBM Watson
                deviceCli.commandCallback=mycommandCallback
           
        
# Disconnect the device and application from the cloud
deviceCli.disconnect()