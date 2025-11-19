# main.py (Pico MicroPython)
from machine import Pin, PWM
import time, sys

# ---------- CONFIG ----------
# Rear (Spark Mini ESCs) - rear left, rear right
RL_ESC_PIN = 0   # GP0
RR_ESC_PIN = 2   # GP2

# Front (L298N) - front left, front right
FL_IN1 = 6
FL_IN2 = 7
FL_EN  = 8

FR_IN1 = 10
FR_IN2 = 11
FR_EN  = 12

# Tuning
ESC_FREQ = 50            # Hz for Spark Mini ESCs
L298_PWM_FREQ = 1000     # PWM freq for L298N EN pins
COMMAND_TIMEOUT_S = 0.6  # watchdog timeout
MAX_FRONT_PERCENT = 100   # cap front (L298N) power to this percentage
RAMP_STEP = 50            # percent per ramp step
RAMP_INTERVAL = 0.05     # seconds per ramp step

# ----------------------------
# Setup hardware
rl_pwm = PWM(Pin(RL_ESC_PIN))
rr_pwm = PWM(Pin(RR_ESC_PIN))
rl_pwm.freq(ESC_FREQ)
rr_pwm.freq(ESC_FREQ)

# L298N pins + PWM
fl_in1 = Pin(FL_IN1, Pin.OUT)
fl_in2 = Pin(FL_IN2, Pin.OUT)
fl_pwm = PWM(Pin(FL_EN)); fl_pwm.freq(L298_PWM_FREQ)

fr_in1 = Pin(FR_IN1, Pin.OUT)
fr_in2 = Pin(FR_IN2, Pin.OUT)
fr_pwm = PWM(Pin(FR_EN)); fr_pwm.freq(L298_PWM_FREQ)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ESC helpers
def speed_to_us(speed):
    speed = clamp(speed, -100, 100)
    return int(1500 + (speed * 10))  # -100 => 1000, +100 => 2000

def us_to_duty(us):
    return int((us / 20000.0) * 65535)

def esc_set(pwm_obj, speed, invert=False):
    if invert:
        speed = -speed
    us = speed_to_us(speed)
    pwm_obj.duty_u16(us_to_duty(us))

# L298N driver class with ramping and max-percent clamp
class L298Motor:
    def __init__(self, in1, in2, pwm_obj, max_percent=MAX_FRONT_PERCENT):
        self.in1 = in1
        self.in2 = in2
        self.pwm = pwm_obj
        self.target = 0
        self.current = 0
        self.max_percent = clamp(max_percent, 0, 100)

    def _apply_scaled(self, speed):
        # speed -100..100, scale by max_percent then apply
        s = clamp(int(speed), -100, 100)
        s = int((s * self.max_percent) / 100.0)
        if s > 0:
            self.in1.high(); self.in2.low()
            duty = int((s / 100.0) * 65535)
        elif s < 0:
            self.in1.low(); self.in2.high()
            duty = int(((-s) / 100.0) * 65535)
        else:
            self.in1.low(); self.in2.low()
            duty = 0
        self.pwm.duty_u16(duty)

    def set_target(self, speed):
        self.target = clamp(int(speed), -100, 100)

    def update_ramp(self, step=RAMP_STEP):
        if self.current == self.target:
            return
        if self.current < self.target:
            self.current = min(self.target, self.current + step)
        else:
            self.current = max(self.target, self.current - step)
        self._apply_scaled(self.current)

    def stop_immediate(self):
        self.current = 0
        self.target = 0
        self._apply_scaled(0)

# instantiate motors
fl_motor = L298Motor(fl_in1, fl_in2, fl_pwm, max_percent=MAX_FRONT_PERCENT)
fr_motor = L298Motor(fr_in1, fr_in2, fr_pwm, max_percent=MAX_FRONT_PERCENT)

# initialize rear ESCs to neutral
esc_set(rl_pwm, 0)
esc_set(rr_pwm, 0)

print("Pico mecanum controller ready!")

# Parser: "Mfl,fr,rl,rr"
def parse_m(line):
    if not line or not line.startswith("M"):
        return None
    try:
        body = line[1:].strip()
        parts = body.split(",")
        if len(parts) != 4:
            return None
        fl = int(parts[0]); fr = int(parts[1]); rl = int(parts[2]); rr = int(parts[3])
        return (-fl, -fr, rl, rr)
    except Exception:
        return None

last_received = time.time()

# non-blocking approach note:
# sys.stdin.readline() on Pico blocks until newline; that's OK because Pi sends frequent commands.
# We'll call update_ramp() regularly when idle to ensure ramping and watchdog behavior.

while True:
    try:
        line = sys.stdin.readline()  # blocks until newline
        if not line:
            # no data - step ramps and check timeout
            fl_motor.update_ramp(); fr_motor.update_ramp()
            if time.time() - last_received > COMMAND_TIMEOUT_S:
                # stop motors
                fl_motor.set_target(0); fr_motor.set_target(0)
                esc_set(rl_pwm, 0); esc_set(rr_pwm, 0)
            time.sleep(RAMP_INTERVAL)
            continue

        line = line.strip()
        if not line:
            fl_motor.update_ramp(); fr_motor.update_ramp()
            time.sleep(RAMP_INTERVAL)
            continue

        parsed = parse_m(line)
        if parsed is None:
            # ignore malformed but keep ramping
            fl_motor.update_ramp(); fr_motor.update_ramp()
            time.sleep(RAMP_INTERVAL)
            continue

        fl_cmd, fr_cmd, rl_cmd, rr_cmd = parsed
        last_received = time.time()

        # Rear ESCs (rear-left, rear-right)
        esc_set(rl_pwm, rl_cmd, invert=True)
        esc_set(rr_pwm, rr_cmd, invert=False)

        # Front L298N targets (will ramp)
        fl_motor.set_target(fl_cmd)
        fr_motor.set_target(fr_cmd)

        # Immediately step ramp once for responsiveness
        fl_motor.update_ramp(); fr_motor.update_ramp()

    except Exception as e:
        # on any error, stop everything safely and continue
        try:
            print("ERR", e)
        except:
            pass
        fl_motor.set_target(0); fr_motor.set_target(0)
        esc_set(rl_pwm, 0); esc_set(rr_pwm, 0)
        time.sleep(RAMP_INTERVAL)
