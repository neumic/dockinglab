#!/usr/bin/env python

import sys
import math
import threading
import nxt.locator
from nxt.motor import *
from nxt.sensor import *

SAMPLE_ITERS = 3

N		= 0
NE		= 45
E		= 90
SE		= 135
S		= 180
SW		= 225
W		= 270
NW		= 315



def meters2tacos(x):
	#WRONG
	return 2050 * x

class thread_wait( threading.Thread ):
	def __init__( self, condition, action):
		threading.Thread.__init__( self )
		self.condition = condition
		self.action = action

	def run( self ):
		while not self.condition():
			pass
		self.action()


class LineBot:
	def __init__(self):
		print 'Looking for brick 7 ...'
		sock = nxt.locator.find_one_brick(host='00:16:53:08:3D:31',
						name='NXT')
		print 'Found brick 7 or timed-out ...'
		if sock:
			print 'Connecting to the brick ...'
			self.brick = sock.connect()
			print 'Connected to the brick or timed-out ...'
			if self.brick:
				self.right = nxt.motor.Motor(self.brick, PORT_B)
				self.left = nxt.motor.Motor(self.brick, PORT_C)
				self.arm = nxt.motor.Motor(self.brick, PORT_A)
				self.light= LightSensor(self.brick, PORT_3)
				self.touch= TouchSensor(self.brick, PORT_1)
				self.compass = UltrasonicSensor(self.brick, PORT_2)
				self.ultrasonic = UltrasonicSensor(self.brick, PORT)
				self.sensor_lock = threading.Lock()

				thread_wait( self.get_touch, self.suicide )
				self.arm_position = -1

				self.line_color = 100

			else:
				print 'Could not connect to NXT brick'
		else:
			print 'No NXT bricks found'

	def go(self, speed=100):
		self.right.run(self.speed)
		self.left.run(self.speed)
	
	def stop(self):
		self.left.stop()
		self.right.stop()

	def rotate_right(self, speed):
		self.left.run(speed)
		self.right.run(-speed)
		
	def rotate_left(self, speed):
		self.left.run(-speed)
		self.right.run(speed)

	def arm_toggle (self):
		self.arm.update(50,90 * self.arm_position)
		self.arm_position *= -1
		

	def suicide(self):
		#print "Dying."
		self.stop()
		self.arm.stop()
		self.light.set_illuminated(False)
		sleep(1)
		
	def get_light_reading(self):
		# Get SAMPLE_ITERS samples from the light senor and returns the average
		total = 0
		self.sensor_lock.aquire()
		for n in range(SAMPLE_ITERS):
			total += self.light.get_sample()
		self.sensor_lock.release()
		value = total / SAMPLE_ITERS
		return value

	def get_heading(self):
		try:
			total = 0
			self.sensor_lock.aquire()
			for n in range(SAMPLE_ITERS):
				total += self.light.get_sample()
			value = total / SAMPLE_ITERS / 2
		except:
			self.sensor_lock.release()
			value = -1
		return value

	def get_touch(self):
		self.sensor_lock.aquire()
		value = self.touch.get_sample()
		self.sensor_lock.release()
		return value

	def reading_spin(self):
		self.arm_toggle()
		sleep(0.5)
		values = []
		start = self.get_heading() - 1
		self.rotate_right(10)
		heading = self.get_heading()
		while heading != start:
			values += (self.get_light_reading(), heading)
			heading = self.get_heading()
		self.stop()
		self.arm_toggle()
		return values
	
	def data_crunch(self, list):
		if len(list):
			total = 0
			for n in list:
				total += n[0]
			average = total / len(list)	
		else:
			average = 0
		for n in list:
			if n[0] > 20 + average:
				return n[1]
		return -1

	def starting_point(self):
		self.turn_to(N)
		self.find_line()
		self.turn_to(W)
		self.find_line()
		self.turn_to(SE)
		self.go_distance(math.sqrt(2) )
		
	def find_line(self):
		self.go()
		while not self.get_light_reading()< self.line_color:
			pass
		self.stop()
		self.go_distance(-0.05)
		
	def go_distance(self, distance):
		#will use for the triangle bit of the finding the light position
		offset = self.right.get_output_state()[9]
		distance = meters2tacos (distance)
		self.go()
		while not self.right.get_output_state() >= offset + distance:
			pass
		self.stop ()

	def turn_to (self, heading):
		#Fix Me!
		self.rotate_right()
		while not self.get_heading() == heading:
			pass
		self.stop()
	
	def approach_wall(self):
		self.go()
		#watch for wall
		#when wall is close:
			#slow
		#drive_distance(small)
	
        def nearest_cardinal_direction(self,n):
                x = n % 90 
                if x <= 45:
                        return n - x 
                else:
                        return n + (90 - x)
                
                
        
def dock(side = "left"):
	bill = DockBot( )
	bill.starting_point( )
	light_location = bill.crunch_data(bill.reading_spin() )
	if side == "left":
		bill.turn_to((bill.nearest_cardinal_direction(light_location)-45)% 360))
        else: #turning to the right 
                bill.turn_to((bill.nearest_cardinal_direction(light_location)+45)% 360))
        bill.go_distance(0.3)
        bill.turn_to(bill.nearest_cardinal_direction(light_location))
	bill.approach_wall( )	
        if side == "left":
		bill.turn_to((bill.nearest_cardinal_direction(light_location)+90)% 360))
        else: #turning to the right 
                bill.turn_to((bill.nearest_cardinal_direction(light_location)-90)% 360))
	bill.go(50)
	
if __name__ == "__main__":
	dock()

