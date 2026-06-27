#include "StormBus.hpp"
#include "MecanumDrive.hpp"

// === define pins (GPIO #) ===
#define UART0_TX 0
#define UART0_RX 1

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


// === STORM Bus ===
// we are the drive board, so only listen for messages addressed to us
StormBus bus = StormBus(Address::drive, PICO_DEBUG_LED);
std::shared_ptr<StormMessage> msg;
// =================


// === actuators ===
SparkMini front_left_m = SparkMini(FL_MOTOR_PWM, FL_ENC_A, FL_ENC_B);
SparkMini front_right_m = SparkMini(FR_MOTOR_PWM, FR_ENC_A, FR_ENC_B);
SparkMini back_left_m = SparkMini(BL_MOTOR_PWM, BL_ENC_A, BL_ENC_B);
SparkMini back_right_m = SparkMini(BR_MOTOR_PWM, BR_ENC_A, BR_ENC_B);

MecanumDrive drivebase = MecanumDrive(front_left_m, front_right_m, back_left_m, back_right_m);
unsigned long LastDriveCommandMs = 0;
bool Led1Blink = false;
unsigned long LastLed1Blink = 0;
// =================


void setup() {
    // perform any actuator/sensor setup here
    drivebase.Init();

    // start communication
    bus.Init();
}


void loop() {
    // if there is a message addressed to us
    if (bus.HasMessage()) {
        // get the message
        msg = bus.GetMessage();

        bool GotDriveCommand = false;

        // and do something diffrent based on what message it is
        switch (msg->type) {
            // standard messages everyone receives
            case Configuration: {
                auto converted = msg->AsConfiguration();

                // bus.CONFIG[converted.ID] = converted.value;

                //TODO: if there are PID constants n stuff then update the drivebase object
                
                break;
            }
            case ConfigComplete: {
                auto converted = msg->AsConfigurationComplete();

                // if we aren't initialized yet, then we can be
                drivebase.SetMotionAllowed(true);
                
                break;
            }
            case RobotVelocity: {
                auto converted = msg->AsRobotVelocity();

                GotDriveCommand = true;

                //TODO: field oriented stuff?
                drivebase.SetVelocity(
                    converted.forward_velocity,
                    converted.sideways_velocity,
                    converted.rotational_velocity,
                    false
                );
                
                break;
            }
            case DriveVelocity: {
                auto converted = msg->AsDriveVelocity();

                GotDriveCommand = true;

                drivebase.SetMotorVelocities(
                    converted.front_left_velocity,
                    converted.front_right_velocity,
                    converted.back_left_velocity,
                    converted.back_right_velocity
                );
                
                break;
            }
            case DriveVoltage: {
                auto converted = msg->AsDriveVoltage();

                GotDriveCommand = true;

                //TODO: measure and pass in battery voltage

                drivebase.SetMotorVoltages(
                    converted.front_left_voltage,
                    converted.front_right_voltage,
                    converted.back_left_voltage,
                    converted.back_right_voltage
                );
                
                break;
            }
            case DriveRaw: {
                auto converted = msg->AsDriveRaw();

                GotDriveCommand = true;

                drivebase.SetMotorRaw(
                    converted.front_left_raw,
                    converted.front_right_raw,
                    converted.back_left_raw,
                    converted.back_right_raw
                );
                
                break;
            }
            default:
                //TODO
                break;
        }

        if (GotDriveCommand) {
            LastDriveCommandMs = millis();
        }
    }

    //TODO: handle checking encoders, controlling velocities, etc.
    front_left_m.Tick();
    front_right_m.Tick();
    back_left_m.Tick();
    back_right_m.Tick();

    drivebase.Tick();

    // debug LEDs
    if ((millis() - LastDriveCommandMs) < 500) {
        //TODO: define this blink period somewhere, and maybe have it be dynamic or something (blink as fast as we are commanded to go?)
        if ((millis() - LastLed1Blink) > 500) {
            Led1Blink = !Led1Blink;
        }

        digitalWrite(DEBUG_LED1, Led1Blink);
    }
}