#pragma once
#include <stdio.h>
#include <stdint.h>

enum Address {
    all = 0,
    computer = 1,
    drive = 2,
    task = 3,
    sensor = 4,
    servo = 5,
    game = 6
};

enum Message {
    Request = 10,
    Heartbeat = 11,
    FirmwareConfiguration = 12,
    ConfigurationComplete = 13,
    RobotVelocity = 20,
    MotorVelocity = 21,
    MotorVoltage = 22,
    MotorOutput = 23,
    MotorFeedback = 24,
    BatteryVoltage = 25,
    TaskCommand = 30,
    TaskResponse = 31,
    SensorResponse = 40,
    ServoCommand = 50,
    GameCommand = 60,
    GameResponse = 61
};

// ========== message typedef struct definitions ==========

// ID 10
typedef struct Request {
    uint8_t ID;
} Request;

// ID 11
typedef struct HeartbeatMessage {
    char b = 0xFF; //TODO FIXME
} HeartbeatMessage;

// ID 12
typedef struct FirmwareConfigurationMessage {
    uint8_t type;
    uint8_t ID;
    //TODO
} FirmwareConfigurationMessage;

// ID 13
typedef struct ConfigurationCompleteMessage {
    //TODO
} ConfigurationCompleteMessage;

// ID 20
typedef struct RobotVelocityMessage {
    int16_t forward_velocity;
    int16_t sideways_velocity;
    int16_t rotational_velocity;
} RobotVelocityMessage;

// ID 21
typedef struct MotorVelocity {
    int16_t front_left_velocity;
    int16_t front_right_velocity;
    int16_t back_left_velocity;
    int16_t back_right_velocity;
} MotorVelocity;

// ID 22
typedef struct MotorVoltage {
    int16_t front_left_voltage;
    int16_t front_right_voltage;
    int16_t back_left_voltage;
    int16_t back_right_voltage;
} MotorVoltage;

// ID 23
typedef struct MotorOutput {
    int16_t front_left_output;
    int16_t front_right_output;
    int16_t back_left_output;
    int16_t back_right_output;
} MotorOutput;

// ID 24
typedef struct MotorFeedback {
    int16_t forward_velocity;
    int16_t sideways_velocity;
    int16_t rotational_velocity;
    int16_t delta_x;
    int16_t delta_y;
    int16_t delta_theta;
} MotorFeedback;

// ID 25
typedef struct BatteryVoltage {
    uint8_t voltage;
} BatteryVoltage;

// ID 30
typedef struct TaskCommand {
    char TEMPORARY;
} TaskCommand;

// ID 31
typedef struct TaskResponse {
    char TEMPORARY;
} TaskResponse;

// ID 40
typedef struct SensorResponse {
    char TEMPORARY;
} SensorResponse;

// ID 50
typedef struct ServoCommand {
    char TEMPORARY;
} ServoCommand;

// ID 60
typedef struct GameCommand {
    char TEMPORARY;
} GameCommand;

// ID 61
typedef struct GameResponse {
    char TEMPORARY;
} GameResponse;

// ================================================

class StormMessage {
public:
    Message type;
    Address address;

    // message conversion methods
    Request AsRequest() {
        Request msg;

        return msg; 
    }

    Heartbeat AsHeartbeat() {
        Heartbeat msg;

        //TODO

        return msg;
    }

    FirmwareConfiguration AsFirmwareConfiguration() {
        FirmwareConfiguration msg;

        //TODO

        return msg;
    }

    ConfigurationComplete AsConfigurationComplete() {
        ConfigurationComplete msg;

        //TODO

        return msg;

    }

    RobotVelocity AsRobotVelocity() {
        //TODO
    }

    MotorVelocity AsMotorVelocity() {
        //TODO
    }

    MotorVoltage AsMotorVoltage() {
        //TODO
    }

    MotorOutput AsMotorOutput() {
        //TODO
    }

    MotorFeedback AsMotorFeedback() {
        //TODO
    }

    BatteryVoltage AsBatteryVoltage() {
        //TODO
    }

    TaskCommand AsTaskCommand() {
        //TODO
    }

    TaskResponse AsTaskResponse() {
        //TODO
    }

    SensorResopnse AsSensorResponse() {
        //TODO
    }

    ServoCommand AsServoCommand() {
        //TODO
    }

    GameCommand AsGameCommand() {
        //TODO
    }

    GameResponse AsGameResponse() {
        //TODO
    }
};