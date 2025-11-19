from machine import Pin, PWM
import time, sys

FREQ = 50  # Standard ESC frequency (50Hz)

left_pwm = PWM(Pin(0))
right_pwm = PWM(Pin(2))

left_pwm.freq(FREQ)
right_pwm.freq(FREQ)

# -------------------------
#   UTILITY FUNCTIONS
# -------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def speed_to_us(speed):
    """
    Convert speed -100..100 to PWM microseconds.
    1500us = stop, 100us per 10% speed.
    """
    speed = clamp(speed, -100, 100)
    return int(1500 + speed * 5)   # 100% = 2000us, -100% = 1000us

def us_to_duty(us):
    """
    Convert microseconds to 16-bit duty for PWM @ 50Hz.
    Period = 20,000us. Duty16 = ratio * 65535.
    """
    return int((us / 20000.0) * 65535)

def set_motor(pwm_obj, speed, invert=False):
    if invert:
        speed = -speed
    duty = us_to_duty(speed_to_us(speed))
    pwm_obj.duty_u16(duty)

# -------------------------
#   STARTUP
# -------------------------

print("Pico motor controller ready!", flush=True)

# Failsafe startup
set_motor(left_pwm, 0)
set_motor(right_pwm, 0)

# -------------------------
#   MAIN LOOP
# -------------------------

BUFFER_LIMIT = 50   # Max characters allowed in serial buffer

while True:
    try:
        # If buffer is overflowing, flush it to avoid lag
        if sys.stdin.buffer_len() > BUFFER_LIMIT:
            sys.stdin.read()    # dump everything
            continue

        line = sys.stdin.readline()

        if not line:
            continue

        line = line.decode().strip()

        # Expect format: L-100R100
        if not ("L" in line and "R" in line):
            continue

        l_index = line.index("L") + 1
        r_index = line.index("R")

        L = int(line[l_index:r_index])
        R = int(line[r_index + 1:])

        set_motor(left_pwm, L, invert=True)
        set_motor(right_pwm, R, invert=False)

    except Exception as e:
        print("ERROR:", e, "line=", line)
        # SAFETY: stop motors on bad data
        set_motor(left_pwm, 0)
        set_motor(right_pwm, 0)
