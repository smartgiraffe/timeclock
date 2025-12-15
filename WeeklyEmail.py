import pandas as pd
from datetime import datetime,timedelta
import time
import subprocess
import os
import smtplib
import ssl
from email.message import EmailMessage
import mimetypes
from escpos.printer import Usb


# Define email sender and receiver
email_sender = 'user@gmail.com'
email_password = '' # the special gmail API password
email_receiver = 'your email recipient'

file_path = "/home/timeclock/users/" #list all the files from the directory
file_list = os.listdir(file_path)
p = Usb(0x0483, 0x5743,0) #0x04b8, 0x0202, 0) # , profile="TM-T88III")

line = ""

with open(f'/home/timeclock/reports/week_ending_{datetime.now():%Y%m%d}-time.csv', "w") as f:
    line = "Week Ending : " + (f'{datetime.now():%Y-%m-%d}') + '\n'
    print(line, file = f)
    print(',Weekday,Clocked In,Clocked Out, Hours\n\n', file = f)
    for file in file_list:
# print the file associated with the user clocking out.
        userName = file[:-4]
        line = userName
        print(line, file = f)

        p.text(userName)
        p.text("\n\n Week Ending : ")
        p.text(f'{datetime.now():%Y-%m-%d}')
        p.text("\n\n\n      IN:                , OUT:               \n")


        ufile= open(file_path + file, "r")
        printfile = ufile.readlines()
        hours = 0
        for xyz in printfile:
            timestamp = datetime(int(xyz[:4]),int(xyz[5:7]),int(xyz[8:10]))
            clockin = datetime.strptime(xyz[:19],'%Y-%m-%d %H:%M:%S')
            clockout = datetime.strptime(xyz[21:40],'%Y-%m-%d %H:%M:%S')
            hours = hours + ((clockout - clockin).total_seconds()/3600)
            day = timestamp.strftime('%A')

            p.text(day[:3])
            p.text('. ')
            p.text(xyz)

            line = ',' + day[:3] + '.,' + xyz[:19] +',' +xyz[21:40] + ',' + f'{((clockout - clockin).total_seconds()/3600):.2f}'
            print(line, file = f)
        p.text('\n\n Total hours worked : ')
        hoursworked = f'{hours:.1f}'
        p.text(hoursworked)
        p.text("\n\n\n\n")
        p.text("I certify that this is a true and correct\n statement of all times reported herein\n for the week shown above.\n\n")
        p.text("Signature:__________________________\n")
        p.cut()
        line = ',,,,' + f'{hours:.2f}'
        print(line,file = f)
        print("\n\n\n", file = f)

#email the weekly file.
filename = f'week_ending_{datetime.now():%Y%m%d}-time.csv'
path = f'/home/timeclock/reports/{filename}'


ctype, encoding = mimetypes.guess_type(path)
if ctype is None or encoding is not None:
    ctype = 'application/octet-stream'
maintype, subtype = ctype.split('/', 1)


# Set the subject and body of the email
subject = f'Time Sheets week ending: {datetime.now():%Y %m %d}'
body = """
Attached is this weeks time summary
"""

em = EmailMessage()
em['From'] = email_sender
em['To'] = email_receiver
em['Subject'] = subject
em.set_content(body)
with open(path, 'rb') as fp:
    em.add_attachment(fp.read(), maintype=maintype, subtype=subtype,
                       filename=filename)


# Add SSL (layer of security)
context = ssl.create_default_context()

# Log in and send the email
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    smtp.login(email_sender, email_password)
    smtp.sendmail(email_sender, email_receiver, em.as_string())
