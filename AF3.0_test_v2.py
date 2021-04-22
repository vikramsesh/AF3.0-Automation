"""
AF3.0 hard water test
Vikram Seshadri
May 21, 2019

"""

import time
import sys
import RPi.GPIO as GPIO
import serial
import re
import datetime

#email
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
import socket


#variables to change
run_time = 30 #Enter number in minutes
startingCycle = 184 #Starting cycle number
max_cycles = 30 #number of cycles
reservoir_volume = 900 #volume in the reservoir in grams
filename_extra = "" #Extra filename
receiver_email = ["vseshadri@sharkninja.com"]

#scale serial
scale_serial = serial.Serial (port = '/dev/ttyUSB0', timeout = 0.5, baudrate = 9600)
scale_serial.flushInput()
scale_serial.flushOutput()

FLOAT = 6
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOAT, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#variables definition
unit_relay = 17
pump_relay = 5
valve_relay = 18
unit_relay_status = 0
pump_relay_status = 0
valve_relay_status = 0

setup_flag = 0
valve_flag = 0
sample_number = 0

cycle_cnt = startingCycle

start_time = 0
start_scale_reading = 0
final_scale_read = 0
filename = ""
csvfile = "/home/pi/Desktop/AF3.0/Data"

#GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(pump_relay, GPIO.OUT)
GPIO.setup(unit_relay, GPIO.OUT)
GPIO.setup(valve_relay, GPIO.OUT)

#email
def email_send(email_message):
    try:
        global receiver_email
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "sninja.test@gmail.com"
        password = '$#!N*&!0'
         
        message = email_message

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            for i in range(0,len(receiver_email)):
                server.sendmail(sender_email, receiver_email[i], message)
    except KeyboardInterrupt:
        stop_eveything()
        print("1. Program Stopped - Keyboard Interrupt")
        sys.exit(1)
            
    except Exception as e:
        print("1." + str(e))
        print ("Failed to send email")

            
#float interrupt
def floatdetect(channel):
    GPIO.output(unit_relay, GPIO.LOW)
    unit_relay_status = 0

    GPIO.output(pump_relay, GPIO.LOW)
    pump_relay_status = 0

    GPIO.output(valve_relay, GPIO.LOW)
    valve_relay_status = 0

    print("Float triggered")
    email_send("AF Tub Overfill")
    exit()

#Reading data from scale
def scale_read():
    try:
            
        global scale_serial

        scale_serial.close()
        scale_serial.open()
        scale_output = scale_serial.readline()
        scale_serial.flushInput()

        y= scale_output.strip()
        y = scale_output.decode("utf-8","replace")

        scale_pattern = r"([\w]+)(,)([\+|-])([\d\.]+)(\s+)([\w]+)"

        match = re.match(scale_pattern,y)
        
        if match is not None:
            #~ print (match.group(3)+match.group(4))
            scale_grams = match.group(3)+match.group(4)

            if float(match.group(4) or 0) < 0 or float(match.group(4) or 0) > 6100:
                print("Scale Error - Power Cycle Scale")
                email_send("AF3.0 Scale Error - Power Cycle Scale. " + " Scale Read(g): " + str(match.group(4)))
                exit()
            return float(match.group(4) or 0)
        
        else: 
            return 0
        
    except KeyboardInterrupt:
        stop_eveything()
        print("2. Program Stopped - Keyboard Interrupt")
        sys.exit(1)
                
    except Exception as e:
        print("2." + str(e))
        
        
#csv header
def csv_header(csvfile_name):
    with open(csvfile_name,'a') as f:
        header = ("{},{},{},{},{},{},{},{}\n").format("Time Stamp","Sample","Volume(mL)","Float Status", "Valve Status", "Unit Status", "Start scale reading","Final scale reading")
        f.write(header)
        f.close()
    return csvfile
    
#writing to csv
def csv_write(csvfile,sample_number,scale_value,start_scale,end_scale):
    with open(csvfile,'a') as f:
        data = ("{},{},{},{},{},{},{},{}\n").format(datetime.datetime.now(),sample_number,scale_value, GPIO.input(FLOAT), valve_relay_status, unit_relay_status,start_scale,end_scale)
        f.write(data)
        f.close()
        print("\nSample: " + str(sample_number) + " Scale: " + str(scale_value))
        print("Float Status: " + str(GPIO.input(FLOAT)) + " Valve status: " + str(valve_relay_status) +" Unit status: " + str(unit_relay_status))
        print("Start scale reading: " + str(start_scale) + " Final scale reading: " + str(end_scale))
    
    return sample_number, scale_value, GPIO.input(FLOAT), valve_relay_status, unit_relay_status, start_scale, end_scale
             
#renaming filename every cycle
def csv_filename():
    global filename, cycle_cnt, filename_extra, run_time, reservoir_volume
    filename = "AF "+ "Volume " + str(reservoir_volume) + "mL " + "RunTime " + str(run_time) +"min" +" Cycle" + str(cycle_cnt) + filename_extra +".csv"
    return filename

#Stop all relays
def stop_eveything():
    GPIO.output(pump_relay, GPIO.LOW)
    pump_relay_status = 0

    GPIO.output(unit_relay, GPIO.LOW)
    unit_relay_status = 0

    GPIO.output(valve_relay, GPIO.LOW)
    valve_relay_status = 0

#setup
def setup():
    global start_time, reservoir_volume, start_scale_reading, unit_relay_status, pump_relay_status, valve_relay_status
    setup_time = 0
    while True:
        try:
            stop_eveything()
            time.sleep(1)   
            print("Hi 1")        
            start_scale_reading = scale_read()
            
            time.sleep(0.9)

            if GPIO.input(FLOAT) == 0:

                if start_scale_reading <= 3000:
                    
                    if start_scale_reading <= 900:
                        print("Below valve")
                        GPIO.output(pump_relay, GPIO.HIGH)
                        pump_relay_status = 1
                        print("Hi 2")
                        while scale_read() <= 900:
                            print("Pump on")
                        start_scale_reading = scale_read()
                    
                    else :
                        GPIO.output(pump_relay, GPIO.HIGH)
                        pump_relay_status = 1
                        print("Pump on")
                    
                    local_start_time = time.clock()
                    print (str(start_scale_reading))
                    print("Hi 3")
                    while scale_read() <= 3000: #scale_read() < reservoir_volume + start_scale_reading or 
                        
                        time.sleep(1)
                        setup_time = time.clock() - local_start_time
                        print("Hi 4")
                        print(" Time: " + str(setup_time * 60) + " Scale(g): " + str(scale_read()))
                        if (setup_time*60) >= 15:
                            print("Refill drum")
                            print ("Program Stopped")
                            
                            stop_eveything()
                            email_send("AF3.0 Refill drum " + "Cycle: "+ str(cycle_cnt) + " Scale Read(g): " + str(scale_read()))
                            exit()
                        
                        elif scale_read() >= 3000:
                            print("Hi 5")
                            break
                            #~ print("Reservoir Overfill")
                            #~ stop_eveything()
                            #~ email_send("AF Reservoir Overfill. Cycle: " + str(cycle_cnt))
                            #~ exit()
                        elif GPIO.input(FLOAT) == 1:
                            print("Float Triggered - Tub Overfill")
                            stop_eveything()
                            email_send("AF Tub Overfill - Float Triggered")
                            exit()
                            
                    GPIO.output(pump_relay, GPIO.LOW)
                    pump_relay_status = 0
                    print("Pump off\n")

                else:
                    print("Hi 6")
                    start_scale_reading = scale_read()
                    #~ print("Reservoir overfill")
                    #~ stop_eveything()
                    #~ email_send(" AF3.0 Reservoir overfill " + "Cycle: " + str(cycle_cnt) + " Scale Read(g): " + str(scale_read()) + "\nCheck for block ")
                    #~ exit()

            else:
                stop_eveything()
                
                if GPIO.input(FLOAT) == 1:
                    print("Tub Overfill")
                    email_send("Tub Overfill " + "Cycle: "+ str(cycle_cnt))
            
                else:
                    print ("Float issues")
                    email_send("Float Issues " + "Cycle: "+ str(cycle_cnt))
                
                exit()
            
            start_time = time.clock()
            break
        
        except Exception as e:
            stop_eveything()
            print("3." + str(e))
            print ("3. Program Stopped")
            
            email_send(str(e))
            sys.exit(1)
            
    return start_time, reservoir_volume, start_scale_reading, unit_relay_status, pump_relay_status, valve_relay_status

#interrupt event
#~ GPIO.add_event_detect(FLOAT, GPIO.RISING , callback=floatdetect, bouncetime = 500)

#main code
while True:
    try:
        while cycle_cnt <= (max_cycles+startingCycle-1):
            elapsed_time = time.clock() - start_time
            if setup_flag == 0:
                
                setup()
                print(csv_filename())
                csvfile = "/home/pi/Desktop/AF3.0/Data/" + filename
                #~ print(str(csvfile))
                print("Cycle: " + str(cycle_cnt))
                csv_header(csvfile)
                setup_flag = 1
                time.sleep(5)
                start_scale_reading = scale_read()
                GPIO.output(unit_relay, GPIO.HIGH)
                print("Unit started\n")

            elif (float(sample_number/60) >= run_time) or GPIO.input(FLOAT) == 1:
                #~ print (elapsed_time)
                stop_eveything()

                time.sleep(5)

                sample_number += 1    
                final_scale_read = scale_read()
                
                csv_scale_value = final_scale_read - start_scale_reading
                csv_write(csvfile,sample_number, abs(csv_scale_value) ,start_scale_reading,final_scale_read)
                if abs(csv_scale_value) > 600 or abs(csv_scale_value) < 45 :
                    print(" Not draining ")
                    stop_eveything()
                    email_send("AF Unit not Draining. "+ "Cycle: " +str(cycle_cnt))
                    sys.exit(1)
                    
                if GPIO.input(FLOAT) == 1:
                    print("Tub Overfill")
                    stop_eveything()
                    email_send("Tub Overfill " + "Cycle: "+ str(cycle_cnt))
                    sys.exit(1)
                    
                break
            
            else:
                unit_relay_status = 1
                time.sleep(1)
                sample_number += 1
                if valve_flag == 0:
                    if (sample_number/60) >= 1: #1 minute
                        GPIO.output(valve_relay, GPIO.HIGH)
                        valve_relay_status = 1
                        print("Valve on")
                        valve_flag = 1
                        
                if (sample_number/60) >= (run_time-1): #1 miniute before end time
                    GPIO.output(valve_relay, GPIO.LOW)
                    valve_relay_status = 0
                    print("Valve off")
                
                while scale_read() is None:
                    continue            
                csv_scale_value = scale_read() - start_scale_reading
                csv_write(csvfile,sample_number,abs(csv_scale_value),start_scale_reading,final_scale_read)
        
        GPIO.output(valve_relay, GPIO.LOW)
        valve_relay_status = 0
        
        setup_flag = 0
        valve_flag = 0
        sample_number = 0               
        final_scale_read = 0
        if cycle_cnt+1 > (max_cycles+startingCycle-1):
            print("Test Completed")
            stop_eveything()
            email_send("Test Completed. Cycle:" + str(cycle_cnt))
            sys.exit(1)
            
        print("Unit Cooldown for 4 min.")
        time.sleep(240) #4 minutes cool down before next cycle
        
        cycle_cnt += 1
        
    except Exception as e:
        stop_eveything()
        print("4." + str(e))
        print ("4. Program Stopped")
        
        email_send(str(e))
        sys.exit(1)

if name == "__main__":
    import sys
    data_dir = os.path.abspath(os.curdir) + "/Data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
