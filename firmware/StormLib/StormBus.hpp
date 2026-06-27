#pragma once
#include <memory>
#include "StormMessage.hpp"
#include <stdlib_noniso.h>

#define BAUD_RATE 9600 //TODO: we can probably do a lot faster, should at least consider increasing to 115200

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
    // === configuration parameters ===
    const int16_t CONFIG[255] = {};
    //TODO: update this array with default values
    // ================================

    StormBus(uint8_t address, uint8_t builtin_led_pin) {
        //TODO: any kind of setup stuff I guess (make Serial and RS485 objects)
        this->address = address;
        this->BUILTIN_LED_PIN = builtin_led_pin;
    }

    ~StormBus() {
        //TODO: should probably do something here...
    }

    bool Init() {
        //TODO FIXME
        RS485.setPins(txPin, dePin, rePin);

        RS485.begin(BAUD_RATE);

        if (address > Address::computer) {
            RS485.receive(); // enable receiving messages
        }
        
        digitalWrite(BUILTIN_LED, HIGH);
    }

    //TODO: rename this to uint8_t GetMessage() and have it return the address
    bool HasMessage() {
        // StormMessage object
        //TODO we should store this in this object or something... so GetMessage() can retrieve it...
        StormMessage msg = StormMessage();

        // minimum message size, according to spec, is 6 bytes
        //FIXME that should be #define'd or something
        if (RS485.available() < 6) {
            return false;
        }
        
        // check for start byte (0xAA)
        if (RS485.read() != START_BYTE) {
            // TODO: read consecutively for this byte maybe ???
            // yes we absolutely need to do that FIXME
            return false;
        }

        //FIXME: I don't think we need all these peek() calls, like, we already checked serial.available()

        //TODO: also handle heartbeat

        // next byte is address
        if (RS480.peek() != -1) {
            auto address = RS485.read();

            //TODO FIXME we should check for just our address or 0 instead
            if (address < 0 || address > Address::game) {
                return false;
            }
        }

        // next byte is size
        if (RS485.peek() != -1) {
            auto size = RS485.read();

            // maximum message size is 16 according to the spec
            //FIXME should that be #define'd somewhere?
            if (size < 0 || size > 16) {
                return false;
            }
        }

        // next bytes are data
        //TODO: read SIZE bytes into DATA

        // read stop byte
        if (RS485.peek() != -1) {
            if (RS485.read() != END_BYTE) {
                return false;
            }
        }

        return false;
    }

    /**
     * Get a StormMessage object.
     * Once you've identified that there's a message for you (via HasMessage()),
     * use this to get a pointer to the message object.
     * then check the message's type/ID to see which one it is,
     * then use the various msg.AsMessgeType() functions to get a struct.
     * alternatively you can work with the raw DATA[] array, if you know what you're doing.
     */
    std::shared_ptr<StormMessage> GetMessage() {
        //TODO
        StormMessage msg = StormMessage();

        auto ptr = std::make_shared<StormMessage>(msg);

        return ptr;
    }

    /**
     * Send a response back to the robot's computer.
     * Use this function to SEND messages FROM your board.
     */
    bool SendResponse(StormMessage msg) {
        RS485.beginTransmission();

        // write start byte
        RS485.write(START_BYTE);

        // write address (always computer for a response)
        RS485.write(Address::computer);

        // write message ID
        RS485.write(msg.type);

        // write size
        RS485.write(msg.size);

        // finally write the data
        for (int i = 0; i < msg.size; i++) {
            RS485.write(msg.DATA[i]);
        }

        // write end byte
        RS485.write(END_BYTE);

        // wait for entire buffer to send
        RS485.flush();

        RS485.endTransmission();

        return true; // return true on success
    }

private:
    // === protocol definitions ===
    const char START_BYTE = 0xAA;
    uint8_t address;
    char DATA[16]; //FIXME ???
    const char END_BYTE = 0x55;
    // ============================

    int BUILTIN_LED_PIN = 25; // default on Pico 2
};