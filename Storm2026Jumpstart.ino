// These define's must be placed at the beginning before #include "TimerInterrupt_Generic.h"
// _TIMERINTERRUPT_LOGLEVEL_ from 0 to 4
// Don't define _TIMERINTERRUPT_LOGLEVEL_ > 0. Only for special ISR debugging only. Can hang the system.
#define TIMER_INTERRUPT_DEBUG 1
#define _TIMERINTERRUPT_LOGLEVEL_ 4

// Can be included as many times as necessary, without `Multiple Definitions` Linker Error
#include "RPi_Pico_TimerInterrupt.h"

// To be included only in main(), .ino with setup() to avoid `Multiple Definitions` Linker Error
#include "RPi_Pico_ISR_Timer.h"


#include <Adafruit_DS3502.h>

Adafruit_DS3502 ds3502 = Adafruit_DS3502();

#define pinSCL 5
#define pinSDA 4

#define pinRW 26

#define pinADC 27

// Init RPI_PICO_Timer
RPI_PICO_Timer ITimer1(1);

RPI_PICO_ISR_Timer ISR_timer;

#ifndef LED_BUILTIN
#define LED_BUILTIN 25
#endif

#define LED_TOGGLE_INTERVAL_MS 1000L


#define TIMER_INTERVAL_MS 1L


// Temporary Input- Delete for whatever actual mechanism is
int targetV = 2;

int currentWiper = 0;
double voltageOut;

// Don't touch because witchcraft occurs here that breaks if I get rid of it
bool TimerHandler(struct repeating_timer *t) {
  (void)t;

  static bool toggle = false;
  static int timeRun = 0;

  ISR_timer.run();

  // Toggle LED every LED_TOGGLE_INTERVAL_MS = 2000ms = 2s
  if (++timeRun == ((LED_TOGGLE_INTERVAL_MS) / TIMER_INTERVAL_MS)) {
    timeRun = 0;

    //timer interrupt toggles pin LED_BUILTIN

    digitalWrite(LED_BUILTIN, toggle);
    toggle = !toggle;
  }

  return true;
}


// Main Control Function
void adjustVoltage() {
  voltageOut = (analogRead(pinADC) / 1023.0 * 3.3);

  switch (targetV) {
    case 2:
      if (voltageOut <= 0.37) {
        currentWiper = currentWiper + 2;
        ds3502.setWiper(currentWiper);
      }

      if (voltageOut >= 0.62) {
        currentWiper = currentWiper - 2;
        ds3502.setWiper(currentWiper);
      }

      break;

    case 4:
      voltageOut = (analogRead(pinADC) / 1023.0 * 3.3);
      if (voltageOut <= 0.87) {
        currentWiper = currentWiper + 2;
        ds3502.setWiper(currentWiper);
      }

      if (voltageOut >= 1.12) {
        currentWiper = currentWiper - 2;
      }
      break;
    case 6:
      voltageOut = (analogRead(pinADC) / 1023.0 * 3.3);
      if (voltageOut <= 1.36) {
        currentWiper = currentWiper + 2;
      }

      if (voltageOut >= 1.61) {
        currentWiper = currentWiper - 2;
        ds3502.setWiper(currentWiper);
      }
      break;
    case 8:
      // Baseline Voltage Ideal = 2.48V
      voltageOut = (analogRead(pinADC) / 1023.0 * 3.3);
      if (voltageOut <= 1.86) {
        currentWiper = currentWiper + 2;
        ds3502.setWiper(currentWiper);
      }
      if (voltageOut >= 2.11) {
        currentWiper = currentWiper - 2;
        ds3502.setWiper(currentWiper);
      }
      break;

    case 10:
      voltageOut = (analogRead(pinADC) / 1023.0 * 3.3);
      if (voltageOut <= 2.36) {
        currentWiper = currentWiper + 2;
        if (currentWiper >= 127) {
          currentWiper = 127;
        }
        ds3502.setWiper(currentWiper);
      }

      if (voltageOut >= 2.61) {
        currentWiper = currentWiper - 2;
      }
      break;
  }
  Serial.print("Current Wiper ");
  Serial.println(currentWiper);
  Serial.print("Read Voltage ");
  Serial.println(voltageOut);
}


////////////////////////////////////////////////

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(115200);
  while (!Serial)
    ;

  Serial.println("Adafruit DS3502 Test");

  if (!ds3502.begin()) {
    Serial.println("Couldn't find DS3502 chip");
    while (1)
      ;
  }

  Serial.println("Found DS3502 chip");

  Serial.print(F("\nStarting ISR_Timers_Array_Simple on "));
  Serial.println(BOARD_NAME);
  Serial.println(RPI_PICO_TIMER_INTERRUPT_VERSION);
  Serial.print(F("CPU Frequency = "));
  Serial.print(F_CPU / 1000000);
  Serial.println(F(" MHz"));

  if (ITimer1.attachInterruptInterval(TIMER_INTERVAL_MS * 1000, TimerHandler)) {
    Serial.print(F("Starting ITimer1 OK, millis() = "));
    Serial.println(millis());
  } else
    Serial.println(F("Can't set ITimer1. Select another freq. or timer"));


  switch (targetV) {
    case 2:
      ds3502.setWiper(25);
      currentWiper = 25;
      Serial.println("2V");
      break;

    case 4:
      ds3502.setWiper(50);
      currentWiper = 50;
      Serial.println("4V");
      break;

    case 6:
      ds3502.setWiper(77);
      currentWiper = 75;
      Serial.println("6V");
      break;

    case 8:
      ds3502.setWiper(105);
      currentWiper = 100;
      Serial.println("8V");
      break;

    case 10:
      ds3502.setWiper(127);
      currentWiper = 127;
      Serial.println("10V");
      break;
  }

  ISR_timer.setInterval(2000L, adjustVoltage);
}



void loop() {
}