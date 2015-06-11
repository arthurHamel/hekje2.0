

import Adafruit_CharLCD as LCD
lcd=LCD.Adafruit_CharLCDPlate()
lcd.clear()
lcd.set_color(1,0,0)
lcd.message('IP Address')
import socket
import os
import urllib2

gw = os.popen("ip -4 route show default").read().split()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((gw[2], 0))
ipaddr = s.getsockname()[0]
gateway = gw[2]
host = socket.gethostname()
a=("IP:\n"+ ipaddr)
print(a)
lcd.message(a)