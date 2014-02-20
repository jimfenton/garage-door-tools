## About

The garage door minder (garaged) is a simple application for generating an SMS (text message) notification when the garage door is left open for a specified period of time. It may be used in conjunction with, or independently of, the garage door control application (garage-door-tools/control) or the OneID-authenticated garage door application (oneid-garage-door).

The garage door minder sends text messages through the [Twilio](https://www.twilio.com) telephony API. To use this, you will need to register for an account on Twilio and fund it for a nominal amount.  The recurring charges are very low (currently $1/month plus 0.75 cents per message sent in the US). An alternative would have been to send the messages through the mobile carrier's email-to-SMS gateway, but that seemed less reliable and does not provide a distinct message source phone number like Twilio.  On many phones, this can be used to generate a distinctive audio alert when a message is received from the minder.

By default, the minder generates a text message when the door has been open for an hour and another message when the door is next closed following an open door alert. The latter message is useful if the alerts are sent to multiple people so that they will know that the alert has been addressed.

You can read more about the garage door minder on [my blog](http://altmode.wordpress.com/2013/10/21/the-garage-door-minder/).

### Python Requirements

This application requires that the [Raspberry Pi GPIO daemon](https://github.com/jimfenton/raspberry-gpio-daemon), used to arbitrate multiple users of the GPIO port and permit access from a non-privileged process, also be installed and running.

## Installation

The garage door minder has been tested on a Raspberry Pi model B running Raspbian Linux.

* The primary configuration file is garaged.cfg, a template for which is included. Copy this file to the /etc directory and edit it.  The "notifyees" value is a list of mobile phone numbers to receive the notifications.  "auth\_token", "from\_number", and "account_sid" are the authentication token, source phone number, and account ID obtained when you register at Twilio.

* Place the source code, garaged.py, in a suitable directory such as /usr/local/sbin

* Copy the init script, gpiod, to /etc/init.d/

* Start the daemon.

## Future work

* Make the configuration and parameterization of the minder configuration more friendly, especially adjustment of the time before sending an alert

* Make alert time sensitive to time-of-day: an open garage door might be more of a concern in the middle of the night than during the day, for example.

## Change log
### 0.1.0
* Initial release
