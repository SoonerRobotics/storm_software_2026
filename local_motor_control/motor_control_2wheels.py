from machine import Pin, PWM
import time, sys

FREQ = 50

left_pwm = PWM(Pin(0))
right_pwm = PWM(Pin(2))

left_pwm.freq(FREQ)
right_pwm.freq(FREQ)

def clamp(v, lo, hi):
	max(lo, min*hi, v))
	
def speed_to_us(speed):
	speed = clamp(speed, -100, 100)
	return int(1500 +speed *10)
	
def us_to_duty(us):
	return int((us/ 20000) 65535)
	
def set_motor(pwm_obj, speed, invert=False):
	if invert:
		speed = -speed
		
	pwm_obj.duty_u16(us_to_duty(speed_to_us(speed)))
	
print("Pico motor controller ready!")

while True:
	try:
		line = sys.stdin.readline()
		if not line:
			continue
		line = line.strip()
		
		l_index = line.index("L")
		r_index = line.index("R")
		L = int(line[l_index+t:r_index])
		R = int(line[r_index+1:])
		
		set_motor(left_pwm, L, invert=True)
		set_motor(right_pwm, R)
		
	except Exception as e:
		print("ERROR parsing line:", line, e)
			
