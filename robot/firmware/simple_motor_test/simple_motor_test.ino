#define LED_PIN 25
#define LEFT_MOTOR_PIN 14
#define RIGHT_MOTOR_PIN 27

// SPARK mini min and max pulse width, in microseconds
#define MIN_MICROS 500
#define MAX_MICROS 2500
#define RANGE_MICROS MAX_MICROS - MIN_MICROS

// #include <stdio.h>
#include <Servo.h>

Servo leftMotor;
Servo rightMotor;

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(LEFT_MOTOR_PIN, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN, OUTPUT);

  leftMotor.attach(LEFT_MOTOR_PIN, MIN_MICROS, MAX_MICROS);
  rightMotor.attach(RIGHT_MOTOR_PIN, MIN_MICROS, MAX_MICROS);

  digitalWrite(LED_PIN, HIGH);
}

void loop() {
  // read in the motor commands (left, right, and direction)
  unsigned int left_abs = Serial.read();
  unsigned int right_abs = Serial.read();
  int direction = Serial.read();

  int leftDirection = 1;
  int rightDirection = -1; // right motor is reversed because they're on opposite sides of each other

  // if (left_abs == -1) {
  //   // no serial data available, kill motors
  //   leftMotor.writeMicroseconds(1500);
  //   rightMotor.writeMicroseconds(1500);
  //   digitalWrite(LED_PIN, LOW);
    // delay(500);
  // } else {
    digitalWrite(LED_PIN, HIGH);

    if (direction & 2 > 0) {
      // right motor goes backwards
      rightDirection *= -1;
    }

    if (direction & 1 > 0) {
      // left motor goes backwards
      leftDirection *= -1;
    }

    // set motors
    leftMotor.writeMicroseconds(500 + (leftDirection * left_abs * 1));
    rightMotor.writeMicroseconds(500 + (rightDirection * right_abs * 1));

    // if we haven't received a command recently, stop us
    // TODO FIXME ????
  // }
  
  // delay(50);
}