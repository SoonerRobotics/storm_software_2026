#include "StormBus.hpp"

//TODO: Define pins

// === STORM Bus ===
const Address ADDRESS = Address.drive;
StormBus bus = StormBus(ADDRESS);
StormMessage msg;
// =================


void setup() {
    //TODO: pinmodes? other stuff? idk

    bus.Init();
}


void loop() {
    bus.Tick(); //TODO ???
    // have StormBus automatically blink LED or something
    if (bus.HasMessage()) {
        msg = bus.GetMessage();

        switch (msg.type) {
            case Message.Configuration:
                auto converted = msg.AsConfigurationMessage();

                if (converted.ConfigID == DrivePID_ID) {
                    drivebase.PIDController.SetP(StormMessage.ConfigValue);
                }
                
                break;
            case Message.Drive:
                auto converted = msg.AsDriveMessage();

                drivebase.Drive(
                    converted.ForwardVelocity,
                    converted.SidewasVelocity,
                    converted.RotationalVelocity
                );

                break;
            default:
                //TODO
        }

        //TODO: handle signal light
    } else if (bus.HeartbeatFail) {
        drivebase.depower();
        shutdown();
    }

    //TODO: handle checking encoders, controlling velocities, etc.
    //TODO: handle debug LEDs
}