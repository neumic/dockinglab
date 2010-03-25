#!/usr/bin/env python

import sys
import math
import threading
import nxt.locator
from nxt.hicompass import *
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
			sleep(0.1)
		self.action()


class DockBot:
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
				self.right			= nxt.motor.Motor(self.brick, PORT_B)
				self.left			= nxt.motor.Motor(self.brick, PORT_A)
				self.arm				= nxt.motor.Motor(self.brick, PORT_C)
				self.light			= LightSensor(self.brick, PORT_2)
				self.touch			= TouchSensor(self.brick, PORT_1)
				self.compass		= CompassSensor(self.brick,PORT_3)
				self.ultrasonic	= UltrasonicSensor(self.brick, PORT_4)
				self.sensor_lock	= threading.Lock()

				self.calibrate()

				kill_switch_thread = thread_wait( self.get_touch, self.stop )
				kill_switch_thread.start()
				self.arm_position = -1

				self.line_color = 100

			else:
				print 'Could not connect to NXT brick'
		else:
			print 'No NXT bricks found'

	def go(self, speed= -128):
		self.sensor_lock.acquire()
		self.right.run(speed)
		self.left.run(speed)
		self.sensor_lock.release()
	
	def stop(self):
		self.sensor_lock.acquire()
		self.left.stop()
		self.right.stop()
		self.arm.stop()
		self.sensor_lock.release()

	def rotate_right(self, speed):
		self.sensor_lock.acquire()
		self.left.run(-speed)
		self.right.run(speed)
		self.sensor_lock.release()
		
	def rotate_left(self, speed):
		self.sensor_lock.acquire()
		self.left.run(speed)
		self.right.run(-speed)
		self.sensor_lock.release()

	def arm_toggle (self):
		self.sensor_lock.acquire()
		offset = self.arm.get_output_state()[9]
		self.go(80 * self.arm_position)
		while not self.arm.get_output_state() >= offset + 90 * self.arm_position:
			pass
		self.stop ()
		self.arm_position *= -1
		self.sensor_lock.release()
		
	def suicide(self):
		#print "Dying."
		self.stop()
		self.sensor_lock.acquire()
		self.light.set_illuminated(False)
		self.sensor_lock.release()
		sleep(1)
		
	def get_light_reading(self):
		# Get SAMPLE_ITERS samples from the light senor and returns the average
		total = 0
		self.sensor_lock.acquire()
		for n in range(SAMPLE_ITERS):
			total += self.light.get_sample()
		self.sensor_lock.release()
		value = total / SAMPLE_ITERS
		return value

	def get_heading(self):
		total = 0
		self.sensor_lock.acquire()
		try:
			for n in range(SAMPLE_ITERS):
				total += self.compass.get_sample()
			value = total / SAMPLE_ITERS / 2
		except:
			self.sensor_lock.release()
			value = -1
		self.sensor_lock.release()
		return value

	def get_relative_heading(self, target):
		total = 0
		self.sensor_lock.acquire()
		try:
			value = self.compass.get_relative_heading(target)
		except:
			self.sensor_lock.release()
			value = -1
		self.sensor_lock.release()
		return value

	def get_touch(self):
		self.sensor_lock.acquire()
		value = self.touch.get_sample()
		self.sensor_lock.release()
		return value
	
	def get_distance(self):
		total = 0
		self.sensor_lock.acquire()
		for n in range(SAMPLE_ITERS):
			total += self.ultrasonic.get_sample()
		value = total / SAMPLE_ITERS
		self.sensor_lock.release()
		return value
	
	def on_line(self):
		return self.get_light_reading() < self.line_color
		

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

	def calibrate(self):
		self.compass.calibrate_mode()
		self.rotate_left(30)
		sleep(10)
		self.stop()
		self.compass.measure_mode()

	def starting_point(self):
		self.turn_to(N)
		self.find_line()
		self.turn_to(W)
		self.find_line()
		self.turn_to(SE)
		self.go_distance(math.sqrt(2) )
		
	def find_line(self):
		self.go()
		thread_wait( self.on_line, self.stop )
		self.go_distance(-0.05)
		
	def go_distance(self, distance):
		#will use for the triangle bit of the finding the light position
		self.sensor_lock.acquire()
		offset = self.right.get_output_state()[9]
		self.sensor_lock.release()
		distance = meters2tacos (distance)
		self.go()
		self.sensor_lock.acquire()
		while not self.right.get_output_state() >= offset + distance:
			pass
		self.sensor_lock.release()
		self.stop ()

	def turn_to (self, heading):
		relative_heading = self.get_relative_heading(heading)
		while abs(relative_heading) > 5:
			if relative_heading < 0:
				self.rotate_right(20)
			else:
				self.rotate_left(20)
			relative_heading = self.get_relative_heading(heading)
		self.stop()
	
	def approach_wall(self):
		self.go()
		#while not get
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
	try:
		bill.starting_point( )
		light_location = bill.data_crunch(bill.reading_spin() )
		if side == "left":
			bill.turn_to((bill.nearest_cardinal_direction(light_location)-45)% 360)
		else: #turning to the right 
			bill.turn_to((bill.nearest_cardinal_direction(light_location)+45)% 360)
		bill.go_distance(0.3)
		bill.turn_to(bill.nearest_cardinal_direction(light_location))
		bill.approach_wall( )	
		if side == "left":
			bill.turn_to((bill.nearest_cardinal_direction(light_location)+90)% 360)
		else: #turning to the right 
			bill.turn_to((bill.nearest_cardinal_direction(light_location)-90)% 360)
		bill.go(50)
	finally:
		bill.stop()
	
if __name__ == "__main__":
	dock()

