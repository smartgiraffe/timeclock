 Not so great at the whole explaining my projects, but I'll give it a go.

The physical part is:

A waveshare 1.3" screen "HAT"

An RFID reader that is configured to output plain text to USB. I went with https://www.amazon.com/dp/B07FD7V6KB

A Piezo buzzer

A Raspberry pi Zero

A Vilros USB adapter with USB and network

A thermal receipt printer (USB). I went with an earlier model of https://www.amazon.com/MUNBYN-Chromebook-Auto-Cutter-High-Speed-ITPP047/dp/B0779WGYHS

I put it all together in a 3d-printed box. I'll see if I can get a pic or two uploaded.

The software part. I broke it down to a handful of python scripts. I'll list them and what they do and I'll put the actual code below. Please keep in mind the I am not a programmer by trade, and much has been cobbled together from trial and error and using snippets and examples of others. So, here goes.

timeclock.py Run at startup. I used supervisor to start and make sure things are always running. Primary script for gathering clock-ins and clock-outs and driving the display

weeklyemail.py Called weekly from cron. responsible for printing timeslips and generating a CSV that is mailed to the supervisor for import into payroll

weeklyreports.sh Called weekly from Cron. Shuts down the timeclock, archives the files, cleans up, and restarts the timeclock.

I have it set up with a few directories.

./users this is where the user clockins are written when they clock out.

./scripts where the scripts live

./reports where reports are written

./config there is a clockins.txt that stores a record of clockins in case the program stops. This file is read every time the program starts so we don't lose anything and a ids.txt that is what associates a user name to an RFID badge. 
