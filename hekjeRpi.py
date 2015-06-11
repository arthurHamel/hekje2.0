
import Adafruit_CharLCD as LCD
lcd=LCD.Adafruit_CharLCDPlate()
lcd.clear()
lcd.message('  Resistivity\n     Meter');

import time
import math
import sys,os
import datetime
import numpy as np


def loadParameters():
	parameters=[0,0,0,0,0,0,0]
	file = open("/home/pi/hekje/config.txt", "r")
	parameters[0]=float(file.readline());#xsize
	parameters[1]=float(file.readline());#ysize
	parameters[2]=float(file.readline());#xstep
	parameters[3]=float(file.readline());#ystep
	parameters[4]=int(file.readline());#zigzag (1/0)
	parameters[5]=int(file.readline());#mode Log
	parameters[6]=int(file.readline());#grid Indent
	file.close();
	return (parameters)

def saveParameters():
	file = open("/home/pi/hekje/config.txt", "w+")
	print('%d\n%d\n%.2f\n%.2f\n%d' %(parameters[0],parameters[1],parameters[2],parameters[3],parameters[4]))
	file.write('%d\n%d\n%.2f\n%.2f\n%d\n%d\n%d' %(parameters[0],parameters[1],parameters[2],parameters[3],parameters[4],parameters[5],parameters[6]))
	file.close();

#create the special characters
lcd.create_char(1, [0,0,4,14,31,0,0,0]) #up
lcd.create_char(2, [0,8,12,14,12,8,0,0])#right
lcd.create_char(3, [0,2,6,14,6,2,0,0])#left
lcd.create_char(4, [0,0,31,14,4,0,0,0])#bottom


def connectSensors():
	errmsg=YRefParam()
	#Get access to your device, connected locally on USB for instance
	YAPI.RegisterHub("usb",errmsg)

def getU(voltage):
	if voltage.isOnline():
		u=voltage.get_currentValue()
	else:
		u=10
	return u

		
def getI(current):
	if current.isOnline():
		i=current.get_currentValue()
	else:
		i=5
	return i

def makeR(u,i):
	if i!=0:
		r=u/i * 2*math.pi
	else:
		r=0.0
	return r

def makeLast10(last10,r):
	if len(last10)<10:
		last10=np.append(last10,r)
	else:
		last10=np.append(last10[1:],r);
	return last10;

#Init:

parameters=loadParameters()
connectSensors()
voltage = YGenericSensor.FindGenericSensor("RXMVOLT1-364E6.genericSensor1")
current = YGenericSensor.FindGenericSensor("RXMVOLT1-364F7.genericSensor1")
if (current.isOnline()):
	a='Current ok -'
else:
	a='Amp not found -'
if (voltage.isOnline()):
	b=' Voltage ok '
else:
	b=' Volt not found '
print(a+b)
lcd.clear()
lcd.message(a+'\n'+b)
time.sleep(0.7)
last10=np.array([makeR(getU(voltage),getI(current)),makeR(getU(voltage),getI(current))])
lcd.set_color(1,0,0)
lcd.clear()
lcd.message('Start new grid \x02\nMenu           \x03')
while True:
	if lcd.is_pressed(LCD.RIGHT):
		parameters[6]+=1
		saveParameters()
		gridID=("%d_%s"%(parameters[5],datetime.datetime.now().strftime("%Y%m%d_%H%M")))
		lcd.clear()
		lcd.message('Grid %d: %dx%d\nRes: %.2fx%.2f'%(parameters[5], parameters[0],parameters[1],parameters[2],parameters[3]))
		time.sleep(1.5)
		xdim=int(parameters[0]/parameters[2])
		ydim=int(parameters[1]/parameters[3])
		mat=np.zeros((xdim,ydim))
		logMode=parameters[5]
		Record=True
		x=0
		while (Record and x<xdim):
			y=0
			Line=True
			lcd.clear()
			lcd.message('\x01 to start\n   newline')
			while Line:
				if (lcd.is_pressed(LCD.UP)): #On commence une ligne (la boucle)
					os.system('mpg321 /home/pi/hekje/sounds/startLine.mp3 &')
					lcd.clear()
					while Line:
						u=getU(voltage)
						i=getI(current)
						r=makeR(u,i)
						if (i<=1.7 or y==0):
							Reset=True
						last10=makeLast10(last10,r)
						mean=np.mean(last10)
						lcd.home()
						lcd.message('   L:%d  P:%d \n  %.2f Ohms'%(x+1,y+1,mean) )
						sys.stdout.write("\r%.3f Ohms  u=%.2f  i=%.2f  L:%d  P:%d "%(mean,u,i,x+1,y+1))
						sys.stdout.flush()
						if ((len (last10)==10) and (max(last10)-min(last10) <=0.07 and logMode!=0 and Reset==True) or (lcd.is_pressed(LCD.UP) and y!=0)):
							lcd.clear()						
							os.system('mpg321 /home/pi/hekje/sounds/ok_point.mp3 &')
							if (x %2 !=0 and parameters[4]==1):
								ymat=ydim-y-1
							else:
								ymat=y
							mat[ymat][x]=mean
							y+=1
							if (y==ydim):
								Line = False
							Reset=False
							np.savetxt("/home/pi/hekje/grids/" + gridID +".csv", mat, delimiter=",")
							for a in range (0,1):
								lcd.message('   L:%d  P:%d \n  %.2f Ohms'%(x+1,y+1,mean))
								time.sleep(0.10)
								lcd.clear()
								time.sleep(0.1)
						elif (lcd.is_pressed(LCD.LEFT)):
							lcd.clear()
							lcd.message('   L:%d  P:%d \n    --Back--'%(x+1,y+1))
							Reset=False
							if (y<0):
								y=y-1
							elif (y==0):
								y=ydim
								x-=1
						elif (lcd.is_pressed(LCD.RIGHT)):
							lcd.clear()
							lcd.message("   L:%d  P:%d \n    --Skip--"%(x+1,y+1))
							
							if (x %2 !=0 and parameters[4]==1):
								ymat=ydim-y-1
							else:
								ymat=y
							mat[ymat][x]=0
							y+=1
							if (y==ydim):
								Line = False
							Reset=False
							os.system('mpg321 /home/pi/hekje/sounds/ok_point.mp3 &')
							time.sleep(2)
							lcd.clear()
						elif (lcd.is_pressed(LCD.SELECT)):
							lcd.clear()
							lcd.message('Quit?       Yes\x02\n             No\x03')
							while 1:
								if (lcd.is_pressed(LCD.RIGHT)):
									Line=False
									Record=False
									break
								elif (lcd.is_pressed(LCD.LEFT)):
									lcd.clear()
									break
						time.sleep(0.20)
			x+=1
		lcd.clear()
		lcd.message('    Finished')
		time.sleep(0.75)
		lcd.clear()
		lcd.message('Start new grid \x02\nMenu           \x03')
	elif lcd.is_pressed(LCD.LEFT):
		lcd.clear()
		lcd.message('      Menu')
		Menu=True
		time.sleep(0.5)
		i=0
		NameParams=('  Grid Size X','  Grid Size Y','  Resolution X', '  Resolution Y', '     ZigZag','    Log mode')
		lcd.clear()
		lcd.message('%s\n\x03     %d     \x02'%(NameParams[i],parameters[i]))
		while Menu:
			if lcd.is_pressed(LCD.UP):
				if (i==5):
					i=0
				else:
					i+=1
				lcd.clear()
				if (i==4 and parameters[i]==1):
					lcdVal='      Yes      '
				elif (i==4 and parameters[i]==0):
					lcdVal='      No     '
				elif (i==2 or i==3):
					lcdVal=('    %.2f    '%parameters[i])
				elif (i==0 or i==1):
					lcdVal=('    %d    '%parameters[i])
				elif (i==5):
					if(parameters[i]==0):
						lcdVal='    Manual    '
					elif(parameters[i]==1):
						lcdVal='  Auto - slow '
					elif(parameters[i]==2):
						lcdVal=' Auto - medium'
					elif(parameters[i]==3):
						lcdVal='  Auto - fast '			
				lcd.clear()
				lcd.message('%s\n\x03%s\x02'%(NameParams[i],lcdVal))
			elif lcd.is_pressed(LCD.LEFT):
				if (i==4 and parameters[i]==1):
					parameters[i]=0
					lcdVal='      No      '
				elif (i==4 and parameters[i]==0):
					parameters[i]=1
					lcdVal='      Yes     '
				elif (i==2 or i==3 and parameters[i]>0):
					parameters[i]-=0.25
					lcdVal=('    %.2f    '%parameters[i])
				elif (i==0 or i==1):
					parameters[i]-=1
					lcdVal=('    %d    '%parameters[i])
				elif (i==5):
					if (parameters[i]==0):
						parameters[i]=3
					else:
						parameters[i]-=1
					if(parameters[i]==0):
						lcdVal='    Manual    '
					elif(parameters[i]==1):
						lcdVal='  Auto - slow '
					elif(parameters[i]==2):
						lcdVal=' Auto - medium'
					elif(parameters[i]==3):
						lcdVal='  Auto - fast '							
				lcd.clear()
				lcd.message('%s\n\x03%s\x02'%(NameParams[i],lcdVal))
			elif lcd.is_pressed(LCD.RIGHT):
				if (i==4 and parameters[i]==1):
					parameters[i]=0
					lcdVal='      No      '
				elif (i==4 and parameters[i]==0):
					parameters[i]=1
					lcdVal='      Yes     '
				elif (i==2 or i==3):
					parameters[i]+=0.25
					lcdVal=('    %.2f    '%parameters[i])	
				elif (i==0 or i==1):
					parameters[i]+=1
					lcdVal=('    %d    '%parameters[i])
				elif (i==5):
					if (parameters[i]==3):
						parameters[i]=0
					else:
						parameters[i]+=1
					if(parameters[i]==0):
						lcdVal='    Manual    '
					elif(parameters[i]==1):
						lcdVal='  Auto - slow '
					elif(parameters[i]==2):
						lcdVal=' Auto - medium'
					elif(parameters[i]==3):
						lcdVal='  Auto - fast '											
				lcd.clear()
				lcd.message('%s\n\x03%s\x02'%(NameParams[i],lcdVal))
			elif lcd.is_pressed(LCD.SELECT):
				saveParameters()
				Menu=False
				lcd.clear()
				lcd.message('Start new grid \x02\nMenu           \x03')
				
	elif lcd.is_pressed(LCD.SELECT):
		time.sleep(2)
		if lcd.is_pressed(LCD.SELECT):		
			lcd.clear()
			lcd.set_color(0,0,0)
			exit();
			print('Exit')
		else: 
			continue




