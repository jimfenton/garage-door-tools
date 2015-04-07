#!/usr/bin/python

# garaged.py - Daemon to generate alerts when garage door is left open
#
# Copyright (c) 2015 Jim Fenton
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

__version__="0.2.0"

import sys
import os
import socket
import stat
import traceback
from datetime import timedelta, datetime, date, time
import time
import daemon
import syslog
import signal
import lockfile
import json
from twilio.rest import TwilioRestClient

# Send a command to the GPIO daemon and return the result
def gpio(s,cmd):
   s.send(cmd+'\n')
   return s.recv(64)[0:-1]

# Send a push notification to the user(s)
# This is called infrequently, so refresh the list of notifyees each time
def notify(state,timestamp):
    if timestamp.date() == datetime.now().date():
        texttime = timestamp.strftime("%I:%M %p")
    else:
        texttime = timestamp.strftime("%d %b %Y %I:%M %p")
            
    syslog.syslog("garaged: door "+state+" since "+texttime)
    try:
        with open("/etc/garaged.cfg","r") as f:
            config = json.load(f)
            f.close()

    except IOError:
        syslog.syslog("garaged: Error accessing garaged configuration")
        return

    if len(config["notifyees"]) == 0:
        syslog.syslog("garaged: No notifyees")
        return
    
    client = TwilioRestClient(config["account_sid"], config["auth_token"])

    if state=="closed":
        msgbody = "Garage door is now closed as of "+texttime
    else:
        msgbody = "Garage door has been "+state+" since "+texttime

    for notifyee in config["notifyees"]:
        message = client.sms.messages.create(body=msgbody, to=notifyee, from_=config["from_number"])
        
def garage_main():

    syslog.syslog("garaged: starting garage_main")

    closedtime = datetime.now()
    validtime = closedtime
    notified = 0

    while 1:
        time.sleep(10)

# Open socket to communicate with gpiod, and determine door state
# TODO: handle collisions with garage door control web app
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sockfile = "/var/run/gpiod.sock"

        s.connect(sockfile)

        doorclosed = gpio(s,"input 24")
        dooropen = gpio(s,"input 26")

        s.close()

# Interpret door state
        if doorclosed == "true":
            if dooropen == "true":
                state = "invalid"
            else:
                state = "closed"
                closedtime = datetime.now()
        else:
            if dooropen == "true":
                state = "open"
            else:
                state = "undetermined"


# Generate notifications as appropriate

        if state == "closed":
            closedtime = datetime.now()
            validtime = closedtime
            if notified > 0:
                notify(state, closedtime)
                notified = 0

        elif state == "open":
            validtime = datetime.now()
            if datetime.now()-closedtime > timedelta(hours=1) and notified != 1:
                notify(state, closedtime)
                notified = 1

        else:
            if datetime.now()-validtime > timedelta(seconds=60) and notified != 2:
                notify(state, validtime)
                notified = 2
                




def program_cleanup():
    conn.close()
    syslog.syslog("garaged: exiting on signal")
    quit()

    # Temporary non-daemon stuff 
#garage_main()
#quit()

context = daemon.DaemonContext(
    pidfile=lockfile.FileLock('/var/run/garaged.pid'),
    )

context.signal_map = {
    signal.SIGHUP: program_cleanup,
    }

with context:
    garage_main()
