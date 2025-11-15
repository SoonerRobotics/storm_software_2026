import pygame
import time
import serial
from math import floor
import struct

pygame.init()

pygame.joystick.init() # I think this is redundant? maybe we don't need
# to initialize the entire pygame module above either, I don't remember

controller = None
#pico = serial.Serial(port="/dev/ttyACM0", baudrate=115200)

def to_uint8(x):
	return floor(x * 255)

# main big loop
while True:
	if controller is None:
		if pygame.joystick.get_count() > 0:
			controller = pygame.joystick.Joystick(0)
			controller.init()
			print("GOT CONTROLLER!")
		else:
			time.sleep(0.5)
	else:
		for event in pygame.event.get(): # pygame event handler loop thingy
			if event.type == pygame.QUIT:
				raise SystemExit # high-tail it outta here
			elif event.type == pygame.JOYAXISMOTION:
				drive = controller.get_axis(0)
				strafe = controller.get_axis(1)
				turn = controller.get_axis(4)
				
				#TODO FIXME add strafing once we like, have more than 2 motors y'know
				left_motor = drive + turn
				right_motor = drive - turn
				
				data = struct.pack("<II", left_motor, right_motor)
				
				#pico.write(data)
				print(data) #TODO FIXME
pygame.quit()
