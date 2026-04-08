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

#define TIMER_INTERVAL_MS 1L

// Init RPI_PICO_Timer
RPI_PICO_Timer ITimer1(1);

RPI_PICO_ISR_Timer ISR_timer;

// Temporary Input- Delete for whatever actual mechanism is
int targetV = 2;

int currentWiper = 0;
double voltageOut;

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

  // Uncomment for testing if need be
  //Serial.print("Current Wiper: ");
  // Serial.println(currentWiper);
  // Serial.print("Read Voltage: ");
  // Serial.println(voltageOut);
}


////////////////////////////////////////////////

void setup() {

  Serial.begin(115200);
  while (!Serial)
    ;

  Wire1.setSCL(pinSCL);
  Wire1.setSDA(pinSDA);
  Wire1.begin();
  

  if (!ds3502.begin(40, &Wire1)) {
    while (1)
      ;
  }

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


// Nothing goes on here, but Arduino freaks out if it isn't there.
void loop() {
}
