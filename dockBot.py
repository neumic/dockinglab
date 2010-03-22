#!/usr/bin/env python

import sys
import math
import nxt.locator
from nxt.motor import *
from nxt.sensor import *

SPEED = 10

def meters2tacos(x):
   #WRONG
   return 2050 * x

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

            self.right_speed = 0
            self.left_speed = 0

         else:
            print 'Could not connect to NXT brick'
      else:
         print 'No NXT bricks found'

   def get_light_reading(self):
      # Get SAMPLE_ITERS samples from the light senor and returns the average
      total = 0
      for n in range(SAMPLE_ITERS):
         total += self.light.get_sample()
      value = total / SAMPLE_ITERS
      return value

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

   def check_dead(self):
      if self.touch.get_sample():
         self.suicide()
         sleep(1)
         while not self.touch.get_sample():
            pass
         self.__init__()

   def suicide(self):
      #print "Dying."
      self.stop()
      self.arm.stop()
      self.light.set_illuminated(False)
      sleep(1)
      
   def set_trace_speeds(self, radius):
      half_wheel_base = 0.5 * self.wheel_base
      left = radius + half_wheel_base
      right = radius - half_wheel_base
      percentage = left/right
      self.left_speed = 50
      self.right_speed = self.left_speed * percentage

   def get_heading(self):
      try:
         return self.compass.get_sample() / 2
      except:
         return -1

   def reading_spin(self):
      values = []
      start = self.get_heading() - 1
      self.rotate_right(10)
      while self.get_heading() != start:
         values += self.get_light_reading()
      self.stop()

         
      

def dock(side = "left"):
   bill = DockBot( )
   bill.find_light( )
   bill.approximate_location( )
   bill.turn_to( closest_cardinal( bill.light_heading( ) ) )
   bill.approach_wall( )
   bill.turn_to( bill.dock_direction( ) )
   bill.drive_till_touch( )
   
if __name__ == "__main__":
   dock()
