# Script for archiving of logs.
# this will be the weekly cleanup and archiving
#—————————————————————–
#!/bin/sh
# Variables Used:
DATE=$(date +%Y%m%d)

supervisorctl stop all
python3 /home/timeclock/scripts/weekly.py
sleep 15s # make sure the python script ran properly
zip /home/timeclock/logs/$DATE-weeklyzip.zip /home/timeclock/csv/*.csv
zip -u /home/timeclock/logs/$DATE-weeklyzip.zip /home/timeclock/users/*.csv
rm /home/timeclock/csv/*
rm /home/timeclock/users/*
supervisorctl reload
