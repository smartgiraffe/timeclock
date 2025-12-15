import keyboard # for capturing scans.
import pandas as pd
from threading import Timer
from datetime import datetime, timedelta
import ast
import os.path
import time
from colorsys import hsv_to_rgb
import board
import subprocess
from digitalio import DigitalInOut, Direction
from PIL import Image, ImageDraw, ImageFont
import json
import RPi.GPIO as GPIO
from escpos.printer import Usb
import spidev as SPI
import ST7789


GPIO.setwarnings(False)


################################
## Filenames
################################
ID_File = "/home/timeclock/config/ids.txt" # Format file notes..
clockins_File = "/home/timeclock/config/clockins.txt" # File format notes
base_dir = "/home/timeclock/csv/"

SEND_REPORT_EVERY = 1 # in seconds, 60 means 1 minute and so on
clockIn = dict()
lastScanTime = dict()


##########################################
## Display stuff here.. 
##########################################
# Create the display
RST = 27
DC = 25
BL = 24
bus = 0
device = 0

# 240x240 display with hardware SPI:
disp = ST7789.ST7789(SPI.SpiDev(bus, device),RST, DC, BL)

disp.Init()
disp.clear()

# for the display screen.. uncomment correct one..
#Dept_name = ""
#Dept_depth = 50

#Dept_name = ""
#Dept_depth = 20

Dept_name = "Department"
Dept_depth = 30

# for generic 2 button
button_A = DigitalInOut(board.D23)
button_A.direction = Direction.INPUT

button_B = DigitalInOut(board.D24)
button_B.direction = Direction.INPUT


width = disp.width
height = disp.height
image = Image.new("RGB", (width, height))
padding = -2
top = padding
bottom = height - padding
x = 0
draw = ImageDraw.Draw(image)

ClockinsSaved = datetime.now()
fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
clock_fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
info_fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

pausedisplay = False
insideRefresh = False 

## Buzzer stuff piezo buzzer on last pins of the pi
beeper = DigitalInOut(board.D21)
beeper.direction = Direction.OUTPUT

# different tones for in and out.
def beepin():
    beeper.value = True
    time.sleep(0.7) # Delay in seconds
    beeper.value = False

def beepout():
    beeper.value = True
    time.sleep(0.2) # Delay in seconds
    beeper.value = False
    time.sleep(0.2)
    beeper.value = True
    time.sleep(0.2) # Delay in seconds
    beeper.value = False

def stopProgram():
# start by witing out any clocked in users to a file
    with open(clockins_File, "w") as f:
        print("{", file=f)
        for userid,timein in clockIn.items():
            print("\""+userid+"\":\""+timein+"\",",file=f)
        print("}", file=f)
#kill the current program
    os._exit(1)


def screenRestart():
    return


def writeScreen(clock,sysinfo,ID, status):

    backlight = DigitalInOut(board.D26)
    backlight.switch_to_output()
    backlight.value = True


    global insideRefresh
    insideRefresh = True
    time.sleep(.01)
    width = disp.width
    height = disp.height
    image = Image.new("RGB", (width, height))
    padding = -2
    top = padding
    bottom = height - padding
    x = 0
    draw = ImageDraw.Draw(image)


    if clock == True:

        this_date = f'{datetime.now():%Y-%m-%d}'
        this_time = f'{datetime.now():%H:%M:%S}'
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw.text((20, 20), "Company", font=clock_fnt, fill="#FF0000")
        draw.text((Dept_depth,50), Dept_name, font=clock_fnt, fill="#FF0000")
        draw.text((20, 150), this_date, font=clock_fnt, fill="#FFFFFF")
        draw.text((20, 180), this_time, font=clock_fnt, fill="#FFFFFF")

    if sysinfo == True:

        draw.rectangle((0, 0, width, height), outline=0, fill=0)
    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
        cmd = "hostname -I | cut -d' ' -f1"
        IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%s MB  %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\''
        Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "cat /sys/class/thermal/thermal_zone0/temp |  awk '{printf \"CPU Temp: %.1f C\", $(NF-0) / 1000}'"  # pylint: disable=line-too-long
        Temp = subprocess.check_output(cmd, shell=True).decode("utf-8")

    # Write four lines of text.
        y = top
        draw.text((x, y), IP, font=info_fnt, fill="#FFFFFF")
        y += info_fnt.getsize(IP)[1]
        draw.text((x, y), CPU, font=info_fnt, fill="#FFFF00")
        y += info_fnt.getsize(CPU)[1]
        draw.text((x, y), MemUsage, font=info_fnt, fill="#00FF00")
        y += info_fnt.getsize(MemUsage)[1]
        draw.text((x, y), Disk, font=info_fnt, fill="#0000FF")
        y += info_fnt.getsize(Disk)[1]
        draw.text((x, y), Temp, font=info_fnt, fill="#FF00FF")

    if clock == False and sysinfo == False:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        y = top
        draw.text((x, y), ID, font=fnt, fill="#FFFFFF")
        y += fnt.getsize(ID)[1]
        draw.text((x, y), status, font=clock_fnt, fill="#FFFFFF")
        y += clock_fnt.getsize(status)[1]
        draw.text((x, y), f'{datetime.now():%H:%M:%S}', font=clock_fnt, fill="#FFFFFF")


    disp.ShowImage(image,0,0)
    if sysinfo == True:
        time.sleep(3)
    if clock == False and sysinfo == False:
        time.sleep(1.5)
    if clock == True:
        time.sleep(.01)

    insideRefresh = False

def lastScan(cardID):
# check to see if the last scan was too close to this one return True if not enough time has passed.
# look for a cardID int the dict. If it exists, get the time, compare it to now. then write now as the time to the dict
    timeBetweenScans = 30 # in seconds
    rightNow = datetime.now()

    if lastScanTime.get(cardID):
        scanTime = datetime.strptime(lastScanTime.get(cardID),"%Y-%m-%d %H:%M:%S")
        lastScanTime[cardID]=f'{datetime.now():%Y-%m-%d %H:%M:%S}'
        secondsSinceLast = (rightNow - scanTime).total_seconds()
        if secondsSinceLast >= timeBetweenScans:
            return True
        else:
            return False

    else:
        lastScanTime[cardID]=f'{datetime.now():%Y-%m-%d %H:%M:%S}'
        return True # no record yet..


def IDScan(cardID):
    timeIn = clockIn.get(cardID)
    if not lastScan(cardID): # has it been more than a period of time since last scan?
        writeScreen(False,False,"Duplicate scan","Try again later.")
        return

    userName = ""
    if userID.get(cardID):
        userName = userID.get(cardID)
    else:
        userName = cardID

    if clockIn.get(cardID):
        # They are clocking out.. remove the data from the dictionary, and write to today's file ID,Time In, Time Out(now)
        beepout()
        InTime = datetime.strptime(clockIn.get(cardID),"%Y-%m-%d %H:%M:%S")
        OutTime = datetime.now()
        print(userName + "," + clockIn.get(cardID) +","+ f'{datetime.now():%Y-%m-%d %H:%M:%S}'+ "," + f'{((OutTime - InTime).total_seconds()/3600):.2f}')
        with open(f'/home/timeclock/csv/{datetime.now():%Y%m%d}-timeclock.csv', "a") as f:
            print(userName + "," + clockIn.get(cardID) +","+ f'{datetime.now():%Y-%m-%d %H:%M:%S}'+ "," + f'{((OutTime - InTime).total_seconds()/3600):.2f}', file = f)

        userFile = '/home/timeclock/users/' + userName + '.csv'

        # write a file out for each user
        with open(userFile, "a") as f:
            print(clockIn.get(cardID) +", "+ f'{datetime.now():%Y-%m-%d %H:%M:%S}', file = f)

        del clockIn[cardID]
        writeScreen(False,False,userName,"Clocked out at:")

        # on Thursday we write the file out to the printer.. 
        if OutTime.weekday() == 9: # 3 for Thurs.. # not using this as we moved the functionality outside
            # print the file associated with the user clocking out.
            p = Usb(0x0483, 0x5743,0) #0x04b8, 0x0202, 0) # , profile="TM-T88III")
            p.text(userName)
            p.text(f'{datetime.now():%Y-%m-%d %H:%M}')
            p.text("\n\n\nIN:                , OUT:               \n")
            ufile= open(userFile, "r")
            printfile = ufile.readlines()
            for xyz in printfile:
                p.text(xyz)
            p.text("\n\n\n\n")
            p.text("I certify that this is a true and correct statement of all times reported herein for the week show above.\n\n")
            p.text("Signature:__________________________\n")
            p.cut()


    else:
        # Every report(see time above) writes the dict out to a logfile so nothing gets lost if we have a problem. 
        beepin()
        clockIn[cardID]=f'{datetime.now():%Y-%m-%d %H:%M:%S}'
        print(userName + "," + clockIn.get(cardID) + ",IN")
        writeScreen(False,False,userName,"Clocked in at:")

class Timeclock:

    def __init__(self, interval, report_method="email"):
        self.interval = interval
        self.report_method = report_method
        # this is the string variable that contains the log of all
        # the keystrokes within `self.interval`
        self.log = ""
        # record start & end datetimes
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()
        self.filename = clockins_File


    def callback(self, event):
        """
        This callback is invoked whenever a keyboard event is occured
        (i.e when a key is released in this example)
        """
        name = event.name
        if len(name) > 1:
            # not a character, special key (e.g ctrl, alt, etc.)
            # uppercase with []
            if name == "space":
                # " " instead of "space"
                name = " "
            elif name == "enter":
                # add a new line whenever an ENTER is pressed
                #OK, let's build a function and call it here. We will pass it self.log which has the ID
                self.log = self.log.replace("enter","")
                IDScan(self.log)
                time.sleep(.01)
                self.log = ""
            elif name == "decimal":
                name = "."
            else:
                # replace spaces with underscores
                name = name.replace(" ", "_")
                name = f"[{name.upper()}]"
                name = name.replace("enter","")
        # finally, add the key name to our global `self.log` variable
        self.log += name

        #print(self.log)

    def update_filename(self):
        # construct the filename to be identified by start & end datetimes
        self.filename = clockins_File

    def report_to_file(self):
        """This method creates a log file in the current directory that contains
        the current keylogs in the `self.log` variable"""
        # open the file in write mode (create it)
        with open(clockins_File, "w") as f:
            # write the keylogs to the file
            print("{", file=f)
            for userid,timein in clockIn.items():
                print("\""+userid+"\":\""+timein+"\",",file=f)
            print("}", file=f)
        clockinsSaved = datetime.now()

    def report(self):
        """
        This function gets called every `self.interval`
        """
#        if not button_A.value:  # left pressed
#            print("Button A(D4) Pressed")
#            writeScreen(False, True, 123,"")

#        if not button_B.value:  # left pressed
#            print("Button B")
#            stopProgram()

        if insideRefresh == False:
            writeScreen(True, False, 123, "")

        if clockinsSaved + timedelta(minutes=10) < datetime.now():
            self.report_to_file()

        timer = Timer(interval=self.interval, function=self.report)
        # set the thread as daemon (dies when main thread die)
        timer.daemon = True
        # start the timer
        timer.start()

    def start(self):
        # record the start datetime
        self.start_dt = datetime.now()
        keyboard.on_release(callback=self.callback)
        self.report()
        # block the current thread, wait until CTRL+C is pressed
        keyboard.wait()

if __name__ == "__main__":

#####################
## Turn the screen on at startup and display system info for 10 seconds
#####################

    clockinsSaved = datetime.now()

    with open(ID_File, "r") as data:
        userID = ast.literal_eval(data.read())
    if os.path.exists(clockins_File):
        with open(clockins_File, "r") as data:
            clockIn = ast.literal_eval(data.read())

    timeclock = Timeclock(interval=SEND_REPORT_EVERY, report_method="file")
    timeclock.start()
