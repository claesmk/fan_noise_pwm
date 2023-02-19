#!/usr/bin/python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import csv
import os
import serial


# Pin configuration
TACH = 24       # Fan's tachometer output pin
PULSE = 2       # Noctua fans puts out two pluses per revolution
waitTime = 1   # [s] Time to wait between each Seraial and print refresh (default 1)
sweepTime = 120 # [s] Total time to sweep from 15-100% PWM

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(TACH, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pull up to 3.3V

# Setup Serial
ser = serial.Serial("/dev/ttyS0", baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
ser.reset_input_buffer()

# Setup variables
t = time.time()
rpm = 0
dList = []
tableList = []
pwm = 15

command = "ON"
print(command)
ser.write(command.encode('utf-8'))

ser.write("D100".encode('utf-8'))


# Caculate pulse frequency and RPM
def fell(n):
    global t
    global rpm
    global dList
    global tableList
    global pwm
    dt = time.time() - t
    if dt < 0.005:
        return  # Reject spuriously short pulses
    dList.append(dt)
    

    freq = 1 / dt
    rpm = (freq / PULSE) * 60
    tableList.append([pwm,rpm])
    
    t = time.time()


# Add event to detect
GPIO.add_event_detect(TACH, GPIO.FALLING, fell)

try:
    while True:
        print("%.f RPM" % rpm)
        rpm = 0
        ser.write("ON".encode('utf-8')) # turns on the fan
        pwm += 85/(sweepTime/waitTime) # calculates how much the pwm needs to be incremented by
        command = f"D{int(pwm):0>3d}" # formats command
        print(command)
        ser.write(command.encode('utf-8')) # sends serial command
        time.sleep(waitTime)  # waits specified time

except KeyboardInterrupt:   # trap a CTRL+C keyboard interrupt
    GPIO.cleanup()          # resets all GPIO ports used by this function
    ser.write("OFF".encode('utf-8')) # turns off fan
    print(dList)
    print(tableList)
    
    def extractDigits(dList):				   #Turns the list of times into something compatible with .csv filetype
        return list(map(lambda el:[el], dList))
    data = extractDigits(dList)
    
    fI = input("Fan Identifier: ")
    
    fileName = "/home/pi/fanData/Fan " + fI + ".csv"       #creates a file with the fan identifier and writes the raw time values to the csv
    file = open(fileName, 'w+', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(data)
        
    curveFile = "/home/pi/fanData/Fan " + fI + " curve.csv"       #creates a file with the fan identifier and writes the curve data to the csv
    file = open(curveFile, 'w+', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(tableList)
    print(f"Saved Files: {fileName} and {curveFile}")
    