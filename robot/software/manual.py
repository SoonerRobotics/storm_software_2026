import pygame
import time
import serial
from math import floor
import struct

pygame.init()

pygame.joystick.init() # I think this is redundant? maybe we don't need
# to initialize the entire pygame module above either, I don't remember

controller = None
pico = None


pico = serial.Serial(port="/dev/ttyACM0", baudrate=115200)

#TODO make a util.py or somethin
def clamp(val, min_, max_):
	if val < min_:
		return min_
	elif val > max_:
		return max_
	return val

# main big loop
while True:
	if pico is None:
		#TODO
		pass
	else:
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
					drive = controller.get_axis(1)
					strafe = controller.get_axis(2)
					turn = controller.get_axis(4)
					
					#TODO FIXME add strafing once we like, have more than 2 motors y'know
					left_motor = drive + turn #also TODO FIXME NORMALIZE THESE!!!
					right_motor = drive - turn
					
					left_motor_abs = floor(abs(left_motor) * 255)
					left_motor_dir = 1 if left_motor < 0 else 0
					
					right_motor_abs = floor(abs(right_motor) * 255)
					right_motor_dir = 2 if right_motor < 0 else 0
					
					# bit-stuffing so this is in one byte instead of two 1-byte booleans
					direction = left_motor_dir | right_motor_dir
					
					#TODO FIXME this will be fine once things get normalized but for now
					left_motor_abs = clamp(left_motor_abs, 0, 255)
					right_motor_abs = clamp(right_motor_abs, 0, 255)
					
					print(left_motor_abs, right_motor_abs, direction)
					
					data = struct.pack(">BBB", left_motor_abs, right_motor_abs, direction)
					
					pico.write(data)
					print(data) #TODO FIXME
pygame.quit()
