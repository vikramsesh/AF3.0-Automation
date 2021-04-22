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

scale_serial = serial.Serial (port = '/dev/ttyUSB0', timeout = 0.5, baudrate = 9600)
scale_serial.flushInput()
scale_serial.flushOutput()

run_time = 30 #Enter number in minutes

FLOAT = 6
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOAT, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#variables definition
unit_relay = 4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
pump_relay = 17
valve_relay = 18

setup_flag = 0

cnt = 0
cycle_cnt = 0
start_scale_reading = 0
final_scale_read = 0
filename = ""
filename_extra = ""

#GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) 
GPIO.setup(pump_relay, GPIO.OUT)
GPIO.setup(unit_relay, GPIO.OUT)
GPIO.setup(valve_relay, GPIO.OUT)

def floatdetect(channel):
    GPIO.output(unit_relay, GPIO.LOW)
    GPIO.output(pump_relay, GPIO.LOW)
    GPIO.output(valve_relay, GPIO.LOW)
    print("Float")
    
#Reading data from scale
def scale_read():
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
        return match.group(4)

#csv header
def csv_header(csvfile):
    with open(csvfile,'a') as f:
        header = ("{},{},{},{},{},{}\n").format("Time Stamp","Sample","Scale(g)","Float Status", "Valve Status")
        f.write(header)
        f.close()
                 
#writing to csv
def csv_write(csvfile,cnt,flow_count,scale_value):
    with open(csvfile,'a') as f:
        data = ("{},{},{},{}\n").format(datetime.datetime.now(),cnt,flow_count,scale_value)
        f.write(data)
        f.close()
        print ("Sample: " + str(cnt) + " Flowrate: " + str(flow_count) + " Scale: " + str(scale_value))

#renaming filename every cycle
def csv_filename():
    global cycle_cnt, filename, run_time, filename_extra
    filename = "AF"+ " Run Time" + str(run_time) +"min." +" Cycle" + str(cycle_cnt) + filename_extra +".csv"
  
    print(filename)  
            
def setup():
    global start_time
    while True:
        try:
            GPIO.output(unit_relay, GPIO.LOW)
            GPIO.output(pump_relay, GPIO.LOW)
            GPIO.output(valve_relay, GPIO.LOW)
            scale_read()
            time.sleep(2)
            local_start_time = time.clock()
            start_scale_reading = float(scale_read())
            time.sleep(2)
            if GPIO.input(FLOAT) == 0:
                
                GPIO.output(pump_relay, GPIO.HIGH)
                print("Pump on")
            
                while float(scale_read()) < (2000 + start_scale_reading) and float(scale_read()) < 3000:
                    elapsed_time = time.clock() - local_start_time
                    if elapsed_time >= 20 or float(scale_read()) >= 3000:
                        GPIO.output(pump_relay, GPIO.LOW)
                        print("Pump off")
                        break
            
                start_time = time.clock()
            
            else:
                if GPIO.input(FLOAT) == 1:
                    print("Water Overfill")
                    
                else:
                    print ("float issues")
                GPIO.output(pump_relay, GPIO.LOW)
                GPIO.output(unit_relay, GPIO.LOW)
                GPIO.output(valve_relay, GPIO.LOW)
                
            
            print(GPIO.input(FLOAT))    
            
        except KeyboardInterrupt:
            GPIO.output(unit_relay, GPIO.LOW)
            GPIO.output(pump_relay, GPIO.LOW)
            exit() 
#~ GPIO.add_event_detect(FLOAT, GPIO.FALLING , callback=floatdetect) 

while True:
    try:
        while cycle_cnt <= (max_cycles+startingCycle-1):
            
            if setup_flag == 0:
                print(GPIO.input(FLOAT))
                setup()
                setup_flag = 1
                
            elapsed_time = time.clock() - start_time
            print(elapsed_time)
            if elapsed_time >= 60 * run_time:
                print (elapsed_time)
                GPIO.output(unit_relay, GPIO.LOW)
                time.sleep(10)
                final_scale_read = float(scale_read())
                exit()  
                
    except KeyboardInterrupt:
        GPIO.output(unit_relay, GPIO.LOW)
        GPIO.output(pump_relay, GPIO.LOW)
        exit()    

if __name__ == "__main__":
    import sys
    if (sys.flags.interactive != 1):
        data_dir = os.path.abspath(os.curdir) + "/Data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

