#pragma once
#include <memory>
#include "StormMessage.hpp"
#include <stdlib_noniso.h>

// configuration parameters -- throw these in a struct?
int16_t linear_velocity_scaler = 3000; // ID 11
int16_t rotational_velocity_scaler = 3500; // ID 12
int16_t motor_velocity_scaler = 100; // ID 13 RENAME because we will have other motors one day
int16_t motor_voltage_scaler = 2500; // ID 14
uint8_t battery_voltage_scaler = 18; // ID 15

// struct StormMessage {
//     char START_BYTE = 0x55;
//     uint8_t address;
//     uint8_t id;
//     utin8_t size;
//     char* data[size];
//     char END_BYTE = 0xAA;
// };

class StormBus {
public:
    StormBus(uint8_t address) {
        //TODO: any kind of setup stuff I guess
        this->address = address;
    }
    ~StormBus() {}

    bool Init() {
        //TODO: Serial.begin() and stuff, and something with the receive enable pins I guess
    }

    //TODO: rename this to uint8_t GetMessage() and have it return the address
    bool HasMessage() {
        //TODO: check if we have a message that we want to listen for
        
        // read until we hit a 0x55
        //TODO

        // next byte is address
        //TODO: check address

        // next byte is size
        //TODO: check size

        // next bytes are data
        //TODO: read SIZE bytes into DATA

        // read stop byte
        //TODO

        //TODO: also handle heartbeat

        return false;
    }

    //FIXME
    std::shared_ptr<StormMessage> GetMessage() {
        //TODO



        return nullptr;
    }

    bool SendResponse(StormMessage msg) {
        return true; // return true on success
    }
private:
    // === protocol definitions ===
    const char START_BYTE = 0x55;
    uint8_t address;
    char DATA[16]; //FIXME ???
    const char END_BYTE = 0xAA;
    // ============================
};