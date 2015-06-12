
import Adafruit_CharLCD as LCD
lcd=LCD.Adafruit_CharLCDPlate()
lcd.clear()
lcd.message('  Resistivity\n     Meter');

from ABE_ADCPi import ADCPi
from ABE_helpers import ABEHelpers
import time
import math
import sys,os
import datetime
import numpy as np

def initADC():
	i2c_helper = ABEHelpers()
	bus = i2c_helper.get_smbus()
	adc = ADCPi(bus, 0x68, 0x69, 12)

def loadParameters():
	parameters=[0,0,0,0,0,0,0]
	file = open("/home/pi/hekje/config.txt", "r")
	for line in file:
		a=file.readline().split("=")
		if (a[0]=="X_SIZE"):
			parameters[0]=float(a[1]);
		elif (a[0]=="Y_SIZE"):
			parameters[1]=float(a[1]);
		elif (a[0]=="X_SPACING"):
			parameters[2]=float(a[1]);
		elif (a[0]=="Y_SPACING"):
			parameters[3]=float(a[1]);
		elif (a[0]=="ZIGZAG"):
			if(a[1]=="YES"):
				parameters[4]=1;
			else:
				parameters[4]=0;
		elif (a[0]=="LOGGING_MODE"):
			if(a[1]=="MANUAL"):
				parameters[5]=0;
			elif(a[1]=="SLOW"):
				parameters[5]=1;
			elif(a[1]=="MEDIUM"):
				parameters[5]=2;
			elif(a[1]=="FAST"):
				parameters[5]=3;
		elif (a[0]=="GRID_INDENT"):
			parameters[6]=int(a[1]);
	file.close();
	return (parameters)

def saveParameters():
	file = open("/home/pi/hekje/config.txt", "w+")
	if parameter[4]==0:
		zigzag="NO"
	elif parameter[4]==1:
		zigzag="YES"
	if parameter[5]==0:
		logging_mode="MANUAL"
	elif parameter[5]==1:
		logging_mode="SLOW"
	elif parameter[5]==2:
		logging_mode="MEDIUM"
	elif parameter[5]==3:
		logging_mode="FAST"
	print('X_SIZE=%d\nY_SIZE=%d\nX_SPACING=%.2f\nY_SPACING=%.2f\nZIGZAG=%s\nLOGGING_MODE=%s\nGRID_INDENT=%d' %(parameters[0],parameters[1],parameters[2],parameters[3],zigzag,logging_mode,parameters[6]))
	file.write('X_SIZE=%d\nY_SIZE=%d\nX_SPACING=%.2f\nY_SPACING=%.2f\nZIGZAG=%s\nLOGGING_MODE=%s\nGRID_INDENT=%d' %(parameters[0],parameters[1],parameters[2],parameters[3],zigzag,logging_mode,parameters[6]))
	file.close();

#create the special characters
lcd.create_char(1, [0,0,4,14,31,0,0,0]) #up
lcd.create_char(2, [0,8,12,14,12,8,0,0])#right
lcd.create_char(3, [0,2,6,14,6,2,0,0])#left
lcd.create_char(4, [0,0,31,14,4,0,0,0])#bottom

def center(s):
	if len(s)<17:
		if (len(s)%2==1):
			numberSpaces=7-len(s)/2
		else:
			numberSpaces=8-len(s)/2
	
		for i in range(0,numberSpaces):
			s=" " + s
	else:
		print('string too long')
		
	return s
	
	

def displayMenu(i):
	NameParams=('  Grid Size X','  Grid Size Y','  Resolution X', '  Resolution Y', '     ZigZag','    Log mode')
	if (i==4 and parameters[i]==0):
		lcdVal=center('No')
	elif (i==4 and parameters[i]==1):
		lcdVal=center('Yes')
	elif (i==2 or i==3):
		lcdVal=center('%.2f'%parameters[i])
	elif (i==0 or i==1):
		lcdVal=center('%d'%parameters[i])
	elif (i==5):
		if(parameters[i]==0):
			lcdVal=center('Manual')
		elif(parameters[i]==1):
			lcdVal=center('Auto - slow')
		elif(parameters[i]==2):
			lcdVal=center('Auto - medium')
		elif(parameters[i]==3):
			lcdVal=center('Auto - fast')					
	lcd.clear()
	lcd.message('%s\n\x03%s\x02'%(NameParams[i],lcdVal))

def getU(voltage):
		
	u=10
	return u

		
def getI(current):

	i=5
	return i

def makeR(u,i):
	if i!=0:
		r=u/i
	else:
		r=0.0
	return r


#Init:

lcd.clear()
lcd.message('New grid \x02\nMenu           \x03')
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
				displayMenu(i)
			elif lcd.is_pressed(LCD.LEFT):
				if (i==4 and parameters[i]==1):
					parameters[i]=0
				elif (i==4 and parameters[i]==0):
					parameters[i]=1
				elif (i==2 or i==3 and parameters[i]>0):
					parameters[i]-=0.25
				elif (i==0 or i==1):
					parameters[i]-=1
				elif (i==5):
					if (parameters[i]==0):
						parameters[i]=3
					else:
						parameters[i]-=1			
				displayMenu(i)
			elif lcd.is_pressed(LCD.RIGHT):
				if (i==4 and parameters[i]==1):
					parameters[i]=0
				elif (i==4 and parameters[i]==0):
					parameters[i]=1
				elif (i==2 or i==3):
					parameters[i]+=0.25
				elif (i==0 or i==1):
					parameters[i]+=1
				elif (i==5):
					if (parameters[i]==3):
						parameters[i]=0
					else:
						parameters[i]+=1										
			elif lcd.is_pressed(LCD.SELECT):
				saveParameters()
				Menu=False
				lcd.clear()
				lcd.message('New grid \x02\nMenu           \x03')
				
	elif lcd.is_pressed(LCD.SELECT):
		time.sleep(2)
		if lcd.is_pressed(LCD.SELECT):		
			lcd.clear()
			lcd.set_color(0,0,0)
			exit();
			print('Exit')
		else: 
			continue




