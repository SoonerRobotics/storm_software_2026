#pragma once
#include <memory>
#include <stdlib_noniso.h>

#include <ArduinoRS485.h>

#include "StormMessage.hpp"


// configuration parameters -- throw these in a struct?
int16_t linear_velocity_scaler = 3000; // ID 11
int16_t rotational_velocity_scaler = 3500; // ID 12
int16_t motor_velocity_scaler = 100; // ID 13 RENAME because we will have other motors one day
int16_t motor_voltage_scaler = 2500; // ID 14
uint8_t battery_voltage_scaler = 18; // ID 15


class StormBus {
public:
    //TODO we will need tx, de, and re pins as well
    StormBus(uint8_t address, uint8_t builtin_led_pin) {
        this->address = address;
        this->BUILTIN_LED_PIN = builtin_led_pin;
    }

    ~StormBus() {
        //TODO: should probably do something here...
    }

    /**
     * TODO: document
     */
    bool Init() {
        //TODO FIXME
        RS485.setPins(this->txPin, this->dePin, this->rePin);

        RS485.begin(BAUD_RATE);

        if (address > Address::computer) {
            RS485.receive(); // enable receiving messages
        }
        
        digitalWrite(this->BUILTIN_LED_PIN, HIGH);

        return true;
    }

    /**
     * TODO: document
     */
    //TODO: rename this to uint8_t GetMessage() and have it return the address
    bool HasMessage() {
        Address tempAddress;
        Message tempType;
        uint8_t tempSize;
        char tempDATA[16];

        // minimum message size, according to spec, is 6 bytes
        if (RS485.available() < this->MIN_MSG_SIZE) {
            return false;
        }
        
        // check for start byte (0xAA)
        bool foundMsg = false;
        while (RS485.peek() != -1) {
            if (RS485.read() == this->START_BYTE) {
                foundMsg = true;
                break;
            }
        }

        if (!foundMsg) {
            return false;
        }

        //FIXME: I don't think we need all these peek() calls, like, we already checked serial.available()

        // next byte is address
        if (RS485.peek() != -1) {
            tempAddress = RS485.read();

            // handle broadcast messages (like heartbeat)
            if (tempAddress == Address::all) {
                //TODO handle heartbeat

                return false; // ???
            } else if (tempAddress != this->address) {
                return false;
            }
        }

        // next byte is type
        if (RS485.peek() != -1) {
            tempType = RS485.read();
        }

        // next byte is size
        if (RS485.peek() != -1) {
            tempSize = RS485.read();

            // maximum message size is 16 according to the spec
            if (tempSize < 0 || tempSize > this->MAX_MSG_SIZE) {
                return false;
            }
        }

        // next bytes are data
        //TODO: read SIZE bytes into DATA
        for (int i = 0; i < tempSize; i++) {
            tempDATA[i] = RS485.read();
        }

        // read stop byte
        if (RS485.peek() != -1) {
            if (RS485.read() != this->END_BYTE) {
                return false;
            }
        }

        //FIXME this will conflict with like, the address variable we should do something
        this->address = tempAddress;
        this->size = tempSize;
        this->type = tempType;

        // transfer DATA too
        for (int i = 0; i < this->size; i++) {
            DATA[i] = tempDATA[i];
        }

        return true;
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
        RS485.write(this->START_BYTE);

        // write address (always computer for a response)
        RS485.write(msg.address);

        // write message ID
        RS485.write(msg.type);

        // write size
        RS485.write(msg.size);

        // finally write the data
        for (int i = 0; i < msg.size; i++) {
            RS485.write(msg.DATA[i]);
        }

        // write end byte
        RS485.write(this->END_BYTE);

        // wait for entire buffer to send
        RS485.flush();

        RS485.endTransmission();

        return true; // return true on success
    }

private:
    // === protocol definitions ===
    const char START_BYTE = 0xAA;
    uint8_t address = 255;
    uint8_t size = 255;
    uint8_t type = 255;
    char DATA[16]; //FIXME ???
    const char END_BYTE = 0x55;
    const unsigned int BAUD_RATE = 115200;

    const uint8_t MAX_DATA_SIZE = 12;
    const uint8_t MIN_DATA_SIZE = 1;
    const uint8_t MAX_MSG_SIZE = 16;
    const uint8_t MIN_MSG_SIZE = 6;
    // ============================

    // pins
    int txPin = 0; //TODO FIXME
    int dePin = 0;
    int rePin = 0;
    int BUILTIN_LED_PIN = 25; // default on Pico 2
};