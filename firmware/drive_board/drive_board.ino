#include "SPARKmini"
#include "QuadratureEncoder"


// === define pins (GPIO #) ===
#define UART0_TX 0
#define UART0_RX 1

#define I2C1_SDA 2
#define I2C1_SDL 3

#define PICO_DEBUG_LED 25
#define DEBUG_LED1 5
#define DEBUG_LED2 6

#define FL_MOTOR_PWM 9
#define FR_MOTOR_PWM 10
#define BL_MOTOR_PWM 11
#define BR_MOTOR_PWM 12

#define FL_ENC_A 13
#define FL_ENC_B 14
#define FR_ENC_A 15
#define FR_ENC_B 16
#define BL_ENC_A 17
#define BL_ENC_B 18
#define BR_ENC_A 19
#define BR_ENC_B 20

#define E_STOP_BUTTON 22

#define BATTERY_VOLTAGE 28
// === /pins ===


// === global variables ===
char* serialBuffer[32]; // default serial buffer size on RP2350 is 32 bytes, although I don't think any message we send comes close to that
uint8_t RobotState = 0; //TODO: make this a bitset? or a class?


void ConfigurePWM() {
    //FIXME
    setAnalogWriteFrequency();

    //TODO: set phase-correct PWM mode?
}

void SetupPIO() {
    //TODO
}

void SetPinModes() {
    //TODO
    SetupPIO();

    //FIXME do we need to configure the communication pins here?

    //TODO: set each GPIO function (Section 9.4, page 589)
    //TODO: also configure the pads (section 9.6, page 595)
    
    pinMode(PICO_DEBUG_LED, OUTPUT);
    pinMode(DEBUG_LED1, OUTPUT);
    pinMode(DEBUG_LED2, OUTPUT);

    pinMode(FL_MOTOR_PWM, OUTPUT);
    pinMode(FR_MOTOR_PWM, OUTPUT);
    pinMode(BL_MOTOR_PWM, OUTPUT);
    pinMode(BR_MOTOR_PWM, OUTPUT);

    //FIXME does this need to be INPUT_PULLUP?
    pinMode(FL_ENC_A, INPUT);
    pinMode(FL_ENC_B, INPUT);
    pinMode(FR_ENC_A, INPUT);
    pinMode(FR_ENC_B, INPUT);
    pinMode(BL_ENC_A, INPUT);
    pinMode(BL_ENC_B, INPUT);
    pinMode(BR_ENC_A, INPUT);
    pinMode(BR_ENC_B, INPUT);

    //FIXME: this already has a pullup, right?
    pinMode(E_STOP_BUTTON, INPUT);

    pinMode(BATTERY_VOLTAGE, INPUT);
}

void SetupSerial() {
    //TODO: configure serial buffer size? other configurable registers?

    // these are the default pins but just in case they get changed
    Serial1.SetTX(UART0_TX);
    Serial1.SetRX(UART0_RX);
    
    Serial1.begin(115200); //TODO: configurable baud rate?

    // slow blink while connecting to serial
    bool serialBlink = false;
    while (!Serial1.available()) {
        if (serialBlink) {
            digitalWrite(PICO_DEBUG_LED, HIGH);
        } else {
            digitalWrite(PICO_DEBUG_LED, LOW);
        }
        delay(200);
        serialBlink = !serialBlink;
    }
}

void SetupI2C() {
    //TODO
}

void setup() {
    //FIXME some of these functions could be like, combined or something...
    // set all the pins to INPUT or OUTPUT (or INPUT_PULLUP / PULLDOWN)
    SetPinModes();

    // set up registers for PWM for the SPARKminis
    ConfigurePWM();

    // set up the serial communication to the Pi
    SetupSerial();

    // set up I2C communication to other boards / sensors
    SetupI2C();
}

void loop() {
    // read commands from Pi via UART
    if (Serial1.available() > 0) {
        uint messageSize = Serial1.readBytesUntil('!', serialBuffer, serialBuffer.size());

        uint msgId = serialBuffer[0];
        if (messageSize > 0) {
            switch (msgId) {
                case 10:
                    // electronics ready message
                    //TODO
                    break;
                case 11:
                    // firmware configuration message
                    //TODO
                    break;
                case 12:
                    // configuration complete message
                    //TODO
                    break;
                case 20:
                    // desired velocity message
                    //TODO
                    break;
                case 21:
                    // motor velocities message
                    //TODO
                    break;
                case 22:
                    // motor voltages message
                    //TODO
                    break;
                case 23:
                    // motor raw % output message
                    //TODO
                    break;

                default:
                    // send an error or set an error state? flash an LED? idk.
                    //TODO
                    break;
            }
        }
    }
}
