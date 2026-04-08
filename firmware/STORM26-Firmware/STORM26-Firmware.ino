
#define SDA 2
#define SCL 3
#define NW_DRV 4 // NW is Front Left
#define NE_DRV 5 // NE is Front Right
#define SW_DRV 6 // SW is Rear Left
#define SE_DRV 7 // SE is Rear Right
#define INTAKE 8
#define SLIDE 9
#define CLIMBER 10
#define CHARGE 11
#define EXTRA_1 12 // IR battery sensor
#define EXTRA_2 13 // arm servo (5 turn)
#define CLAW_1 14 // wrist servo
#define CLAW_2 15 // claw
#define CLAW_3_LARGE 16 // not used
#define JUMPSTART 26
#define SWITCH_1 18 // linear slide limit switch
#define SWITCH_2 19

#define LED_PIN 25

#define TIMEOUT_MS 200

// servo positions FIXME update these whenever they change in constants.toml
// I don't necessarily like hard-coded configurations... maybe on the Pico's filesystem would be better?
#define CLAW_DEFAULT 33
#define WRIST_DEFAULT 127
#define ARM_DEFAULT 204

#define TIMER_INTERRUPT_DEBUG 1
#define _TIMERINTERRUPT_LOGLEVEL_ 4

#include "RPi_Pico_TimerInterrupt.h"
#include "RPi_Pico_ISR_Timer.h"
#include <Wire.h>
#include <Adafruit_DS3502.h>

Adafruit_DS3502 ds3502 = Adafruit_DS3502();

#define pinSCL 3
#define pinSDA 2
#define pinADC 26

#define TIMER_INTERVAL_MS 500L

// Init RPI_PICO_Timer
RPI_PICO_Timer ITimer1(1);

RPI_PICO_ISR_Timer ISR_timer;

// Temporary Input- Delete for whatever actual mechanism is
int targetV = 2;

int currentWiper = 0;
double voltageOut = 0.0;

const int MOTOR_FREQ = 333;
char data[14];
unsigned long lastTime = 0;
bool timed_out = false;
bool connected = false;

bool TimerHandler(struct repeating_timer *t) {
  (void)t;

  static bool toggle = false;
  static int timeRun = 0;

  ISR_timer.run();

  return true;
}


// Main Control Function
void adjustVoltage() {
  voltageOut = (analogRead(pinADC) / 1023.0 * 3.3);

  switch (targetV) {
    case 2:
      if (voltageOut <= 0.51) {
        currentWiper = currentWiper + 2;
      }
      if (voltageOut >= 0.84) {
        currentWiper = currentWiper - 2;
      }

      break;

    case 4:     
      if (voltageOut <= 1.18) {
        currentWiper = currentWiper + 2;
      }
      if (voltageOut >= 1.52) {
        currentWiper = currentWiper - 2;
      }
      break;

    case 6:
      if (voltageOut <= 1.86) {
        currentWiper = currentWiper + 2;
      }
      if (voltageOut >= 2.2) {
        currentWiper = currentWiper - 2;
      }
      break;
    
    case 8:
      if (voltageOut <= 2.53) {
        currentWiper = currentWiper + 2;
      }
      if (voltageOut >= 2.87) {
        currentWiper = currentWiper - 2;
      }
      break;

    case 10:
      if (voltageOut <= 3.21) {
        currentWiper = currentWiper + 2;
      }
      if (voltageOut >= 3.55) {
        currentWiper = currentWiper - 2;
      }
      break;
  }

  if (currentWiper <= 0) {
    currentWiper = 0;
  } else if (currentWiper >= 127) {
    currentWiper = 127;
  } 

  ds3502.setWiper(currentWiper);
}

void setup() {
  pinMode(SWITCH_1, INPUT_PULLUP); // no need for pullup
  pinMode(SWITCH_2, INPUT);

  pinMode(NW_DRV, OUTPUT);
  pinMode(NE_DRV, OUTPUT);
  pinMode(SW_DRV, OUTPUT);
  pinMode(SE_DRV, OUTPUT);
  pinMode(INTAKE, OUTPUT);
  pinMode(SLIDE, OUTPUT);
  pinMode(CLIMBER, OUTPUT);
  pinMode(CHARGE, OUTPUT);
  pinMode(EXTRA_1, INPUT);
  pinMode(EXTRA_2, OUTPUT);
  pinMode(CLAW_1, OUTPUT);
  pinMode(CLAW_2, OUTPUT);
  pinMode(CLAW_3_LARGE, OUTPUT);
  pinMode(JUMPSTART, INPUT); //FIXME this is the ADC pin right?

  pinMode(LED_PIN, OUTPUT);

  analogWriteFreq(MOTOR_FREQ);
  analogWriteResolution(8);

  digitalWrite(LED_PIN, HIGH);


  Serial.begin(115200);

  Wire1.setSCL(pinSCL);
  Wire1.setSDA(pinSDA);
  Wire1.begin();
  
  //FIXME idk if we want to include this here
  // if (!ds3502.begin(40, &Wire1)) {
    // while (1)
      // ;
  // }

  ds3502.begin(40, &Wire1);


  ITimer1.attachInterruptInterval(TIMER_INTERVAL_MS * 1000, TimerHandler);

  switch (targetV) {
    case 2: 
      currentWiper = 25;
      break;

    case 4:
      currentWiper = 50;
      break;

    case 6:
      currentWiper = 77;
      break;

    case 8:
      currentWiper = 100;
      break;

    case 10:
      currentWiper = 127;
      break;
  }

  ds3502.setWiper(currentWiper);

  ISR_timer.setInterval(500L, adjustVoltage);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() >= 14) {
    // digitalWrite(LED_PIN, HIGH);
    Serial.readBytes(data, 14);

    lastTime = millis();
    timed_out = false;
  }

  if((data[0] == '$') && (data[13] == '!') && !timed_out && connected) {
    analogWrite(NW_DRV, data[1]);
    analogWrite(SW_DRV, data[2]);
    analogWrite(NE_DRV, data[3]);
    analogWrite(SE_DRV, data[4]);
    if (digitalRead(SWITCH_1)) {
      analogWrite(SLIDE, data[5]);
    } else {
      analogWrite(SLIDE, 127);
    }
    analogWrite(INTAKE, data[6]);
    analogWrite(EXTRA_2, data[7]);
    analogWrite(CLAW_1, data[8]);
    analogWrite(CLAW_2, data[9]);
    analogWrite(CLIMBER, data[10]);
    // analogWrite(CHARGE, data[11]); // no charging wheel, in software packet this is actually jumpstart...
    targetV = data[11];

    connected = data[12]; // for loss of signal

    digitalWrite(LED_PIN, LOW);
  }

  // firmware watchdog / sort of e-stop
  if ((millis() - lastTime) > TIMEOUT_MS) {
    timed_out = true;

    digitalWrite(NW_DRV, LOW);
    digitalWrite(SW_DRV, LOW);
    digitalWrite(NE_DRV, LOW);
    digitalWrite(SE_DRV, LOW);
    digitalWrite(SLIDE, LOW);
    digitalWrite(INTAKE, LOW);

    digitalWrite(CLAW_1, WRIST_DEFAULT); //FIXME servos should go to their STOW positions
    digitalWrite(CLAW_2, CLAW_DEFAULT); // make sure to keep up to date with constants.toml
    digitalWrite(EXTRA_2, ARM_DEFAULT);
    
    digitalWrite(CLIMBER, LOW);
    // analogWrite(CHARGE, data[11]); // no charging wheel, in software packet this is actually jumpstart...
    
    //TODO turn off jumpstart?
    connected = false;

    digitalWrite(LED_PIN, HIGH);
  }
}
