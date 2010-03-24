#!/usr/bin/env python

import sys
import math
import threading
import nxt.locator
from nxt.motor import *
from nxt.sensor import *

SAMPLE_ITERS = 3
SPEED = 10

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

				self.right_speed = 0
				self.left_speed = 0
				thread_wait( self.get_touch, self.suicide )
				self.arm_speed = 0

				self.line_color = 100

			else:
				print 'Could not connect to NXT brick'
		else:
			print 'No NXT bricks found'

	def go(self):
		print "Going..." + str(self.left_speed) + ":" + str(self.right_speed)
		self.right.run(self.right_speed)
		self.left.run(self.left_speed)
	
	def stop(self):
		self.left.stop()
		self.right.stop()

	def rotate_right(self, speed):
		self.left.run(speed)
		self.right.run(-speed)
		
	def rotate_left(self, speed):
		self.left.run(-speed)
		self.right.run(speed)

	def rotate_arm (self,speed):
		self.arm.update(speed,00)

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
		values = []
		start = self.get_heading() - 1
		self.rotate_right(10)
		while self.get_heading() != start:
			values += self.get_light_reading()
		self.stop()
		#FINISH

	def starting_point(self):
		self.turn_to(NORTH)
		self.arm()
		self.find_line
		self.arm()
		
	def find_line(self):
		self.go()
		while not self.get_light_reading()< self.line_color:
			pass
		self.stop()
		self.go_distance (-10)
		
		if value < self.line_color
		
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
		

def dock(side = "left"):
	bill = DockBot( )
	bill.starting_point( )
	bill.approach_wall( )
	bill.turn_to( bill.dock_direction( ) )
	bill.drive_till_touch( )
	
if __name__ == "__main__":
	dock()

