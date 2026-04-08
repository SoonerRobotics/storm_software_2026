
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
#define CLAW_3_LARGE 16 // Safety Lights
#define JUMPSTART 26
#define SWITCH_1 18 // linear slide limit switch
#define SWITCH_2 19

#define LED_PIN 25

#define TIMEOUT_MS 200

// servo positions FIXME update these whenever they change in constants.toml
// I don't necessarily like hard-coded configurations... maybe on the Pico's filesystem would be better?
#define CLAW_DEFAULT 33
#define WRIST_DEFAULT 127
#define ARM_DEFAULT 178

#include <Wire.h>
#include <Adafruit_DS3502.h>
#include <Adafruit_NeoPixel.h>

// Safety Lights

static const int BLINK_PERIOD_MS = 500;
static const int DEFAULT_BRIGHTNESS = 50;

static const int CLED_COUNT = 21;
static const int CLED_PIN = CLAW_3_LARGE;

int current_brightness = DEFAULT_BRIGHTNESS;
int current_blink_period = BLINK_PERIOD_MS;
int current_color = strip.Color(255, 105, 180);

Adafruit_NeoPixel strip(CLED_COUNT, CLED_PIN, NEO_GRB);

Adafruit_DS3502 ds3502 = Adafruit_DS3502();

#define TIMER_INTERVAL_MS 500L

// jumpstart stuff
int targetV = 2;
int currentWiper = 0;
double voltageOut = 0.0;

const int MOTOR_FREQ = 333;
char data[14];
unsigned long lastTime = 0;

// loss-of-serial / loss-of-signal
bool timed_out = false;
bool connected = false;

// Main Control Function
void adjustVoltage(int target) {
  voltageOut = (analogRead(JUMPSTART) / 1023.0 * 3.3);

  switch (target) {
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

  // ds3502.setWiper(currentWiper);
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

  // Wire1.setSCL(SCL);
  // Wire1.setSDA(SDA);
  // Wire1.begin();
  
  //FIXME idk if we want to include this here
  // if (!ds3502.begin(40, &Wire1)) {
    // while (1)
      // ;
  // }

  // ds3502.begin(40, &Wire1);
  // ds3502.setWiper(25);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() >= 14) {
    // digitalWrite(LED_PIN, HIGH);
    Serial.readBytes(data, 14);

    lastTime = millis();
    timed_out = false;
  }

  if((data[0] == '$') && (data[13] == '!') && !timed_out) {
    connected = data[12]; // for loss of signal
    
    if (connected) {
      // Blink safety lights
      if ((millis() / current_blink_period) % 2 == 0) {
              strip.fill(current_color);
          } else {
              strip.fill(0);
          }
          strip.show();
        
      analogWrite(NW_DRV, data[1]);
      analogWrite(SW_DRV, data[2]);
      analogWrite(NE_DRV, data[3]);
      analogWrite(SE_DRV, data[4]);
      
      // linear slide limit switch check
      if (!digitalRead(SWITCH_1)) {
        // only let us go backwards
        if (data[5] <= 127) {
          analogWrite(SLIDE, data[5]);
        } else {
          //TODO do we want this to be a digitalWrite(0) instead to like, completely turn the motor controller off?
          analogWrite(SLIDE, 127);
        }
      } else {
        analogWrite(SLIDE, data[5]);
      }
      
      analogWrite(INTAKE, data[6]);
      analogWrite(EXTRA_2, data[7]);
      analogWrite(CLAW_1, data[8]);
      analogWrite(CLAW_2, data[9]);
      analogWrite(CLIMBER, data[10]);
      
      // jumpstart stuff
      adjustVoltage(data[11]);

      digitalWrite(LED_PIN, LOW);
    }
  }

  // firmware watchdog / sort of e-stop
  if ((millis() - lastTime) > TIMEOUT_MS) {
    // Solid Safety light color
    strip.fill(current_color);
    strip.show();

    timed_out = true;

    digitalWrite(NW_DRV, LOW);
    digitalWrite(SW_DRV, LOW);
    digitalWrite(NE_DRV, LOW);
    digitalWrite(SE_DRV, LOW);
    digitalWrite(SLIDE, LOW);
    digitalWrite(INTAKE, LOW);

    analogWrite(CLAW_1, WRIST_DEFAULT); //FIXME servos should go to their STOW positions
    analogWrite(CLAW_2, CLAW_DEFAULT); // make sure to keep up to date with constants.toml
    analogWrite(EXTRA_2, ARM_DEFAULT);
    
    digitalWrite(CLIMBER, LOW);
    // analogWrite(CHARGE, data[11]); // no charging wheel, in software packet this is actually jumpstart...
    
    //TODO turn off jumpstart?
    connected = false;

    digitalWrite(LED_PIN, HIGH);
  }
}
