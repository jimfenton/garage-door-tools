#!/usr/bin/python

# operate.py - Check authorization and operate the garage door
#
# Copyright (c) 2014 Jim Fenton
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

import cgi

import sys
import os
import socket
import time
import syslog
import json

# Debugging
import cgitb
cgitb.enable()

# Send a command to the GPIO daemon and return the result
def gpio(cmd):
   s.send(cmd+'\n')
   return s.recv(64)[0:-1]

print """Content-Type: text/html

<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html>
<head>
  <title>Garage Door</title>
  <meta name="viewport" content="width=device-width"/>
</head>
<body>
<div align="center">
<img src="/GarageClosed.png"/>
"""

form = cgi.FieldStorage()
if "key" not in form:
   print "<H1>Error</H1>"
   print "Authentication failure - key not found"
   print "</body></html>"
   exit()

try:
   with open("garage.cfg","r") as f:
      userlist = json.load(f)
      f.close()

except IOError:
   userlist = {}

# If username field exists in the called parameters, we are just being called back to add username to an existing key.

if "username" in form:
   key = form["key"].value
   if key in userlist:
      userlist[key] = form["username"].value
      try:
         with open("garage.cfg","w") as f:
            json.dump(userlist, f)
            f.close()
            syslog.syslog("Description added: "+userlist[key])
      except IOError:
         print "<h2>Error: Unable to add description</h2>"
         syslog.syslog("Error adding user description: "+userlist[key])

      print "<h2>"+userlist[key]+" authorized</h2>"
   else:
      print "<h2>Authorized key not found to bind description</h2>"

   print "</div></body></html>"

   exit()
      

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sockfile = "/var/run/gpiod.sock"

s.connect(sockfile)

key =form["key"].value

descrip = "*"+key[-4:]

mode = gpio("input 12")

if mode == "true":  #Normal mode, LEARN not pressed

   if key in userlist:
      descrip = userlist[key] + " ("+descrip+")" # full description now available
      try:
         if gpio("output 11 high") != "ok":
            raise RuntimeError
         if gpio("output 16 high") != "ok":
            raise RuntimeError
         time.sleep(0.5)
         if gpio("output 11 low") != "ok":
            raise RuntimeError
         if gpio("output 16 low") != "ok":
            raise RuntimeError
         syslog.syslog("Door operated for "+descrip)
         print "<h2>Door operating</h2>"
      except RuntimeError:
         print "<h2>Error response from gpiod</h2>"
   else:
      print "<h2>User not authorized</h2>"
      syslog.syslog("Unauthorized user "+descrip)

elif mode == "false":  # LEARN mode

   if key in userlist:
      descrip = userlist[key] + " ("+descrip+")" # full description now available
      print "<h2>User "+descrip+" already authorized</h2>"
      syslog.syslog("User "+descrip+" already authorized")
   else:
      userlist[key]=""
      try:
         with open("garage.cfg","w") as f:
            json.dump(userlist, f)
            f.close()
            print "<h2>Please enter name/ID of user: </h2>"
            print '<form id="usernameform" method="post">'
            print '<input type="hidden" name="key" value="'+key+'">'
            print 'Username: <input type="text" name="username" size="30">'
            print '<input type="submit" value="Submit"">'
            print '</form>'
            syslog.syslog("User authorization added: "+descrip)
      except IOError:
         print "<h2>Error: Unable to add user authorization</h2>"
         syslog.syslog("Error adding user authorization: "+descrip)

else:
   print "<h2>Error: Unable to read LEARN button</h2>"

print "</div></body></html>"
