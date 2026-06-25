#include "StormBus.hpp"

//TODO: Define pins

// === STORM Bus ===
// we are the drive board, so only listen for messages addressed to us
StormBus bus = StormBus(Address.drive, PIN_LED_BUILTIN);
std::shared_ptr<StormMessage> msg;
// =================

// MecanumDrive drivebase = MecanumDrive(); //TODO

void setup() {
    //TODO: pinmodes? other stuff? idk

    //drivebase.Init();

    // start communication
    bus.Init();
}


void loop() {
    //TODO: have StormBus automatically blink LED or something

    // if there is a message addressed to us
    if (bus.HasMessage()) {
        // get the message
        msg = bus.GetMessage();

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

                //TODO: if we aren't initialized yet, then we can be
                //drivebase.SetMotionAllowed(true);
                
                break;
            }
            case RobotVelocity: {
                auto converted = msg->AsRobotVelocity();

                //TODO
                //drivebase.drive(converted.forward, converted.sideways, converted.rotational);
                
                break;
            }
            case DriveVelocity: {
                auto converted = msg->AsDriveVelocity();

                //TODO
                //drivebase.drive(converted.forward, converted.sideways, converted.rotational);
                
                break;
            }
            case DriveVoltage: {
                auto converted = msg->AsDriveVoltage();

                //TODO
                //drivebase.drive(converted.forward, converted.sideways, converted.rotational);
                
                break;
            }
            case DriveRaw: {
                auto converted = msg->AsDriveRaw();

                //TODO
                //drivebase.drive(converted.forward, converted.sideways, converted.rotational);
                
                break;
            }
            default:
                //TODO
                break;
        }
    }

    //TODO: handle checking encoders, controlling velocities, etc.
    //TODO: handle debug LEDs (blink as fast as we are trying to go, as % of max or something)
}