#define LED_PIN 25
#define LEFT_MOTOR_PIN 14
#define RIGHT_MOTOR_PIN 27

// SPARK mini min and max pulse width, in microseconds
#define MIN_MICROS 500
#define MAX_MICROS 2500

// #include <stdio.h> 
#include <Servo.h>

Servo leftMotor;
Servo rightMotor;

int motorSpeed = 90; // if less than 200, treated as an angle for a Servo by the <Servo.h> library, so 90 degrees should be neutral / no speed.
int direction = 1; // positive is forwards, -1 is reverse
int safety = 30; // I don't trust anything or anyone anymore.

void setup() {
  // Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(LEFT_MOTOR_PIN, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN, OUTPUT);

  leftMotor.attach(LEFT_MOTOR_PIN, MIN_MICROS, MAX_MICROS);
  rightMotor.attach(RIGHT_MOTOR_PIN, MIN_MICROS, MAX_MICROS);

  digitalWrite(LED_PIN, HIGH);
}

void loop() {
  // sweep from stopped to full forwards to full reverse and back
  if (motorSpeed <= (0 + safety)) {
    direction = 1;
  } else if (motorSpeed >= (180 - safety)) {
    direction = -1;
  }

  motorSpeed += direction;

  motorSpeed = 1800;

  leftMotor.writeMicroseconds(motorSpeed);
  rightMotor.writeMicroseconds(motorSpeed); // they're on opposite sides, so reverse the direction

  // blink LED because we can
  // digitalWrite(LED_PIN, HIGH);
  // delay(200);
  // digitalWrite(LED_PIN, LOW);
  // delay(200);
}