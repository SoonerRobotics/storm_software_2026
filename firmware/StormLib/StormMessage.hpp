#pragma once
#include <stdint.h>

/**
 * Unique number indicating who the message is for.
 * Only the computer (#1) can send messages on its own initiative.
 * If more boards are created, add them after the "game" board.
 * The special address number 0 indicates the message is for all boards.
 */
enum Address {
    all = 0,
    computer = 1,
    drive = 2,
    task = 3,
    sensor = 4,
    servo = 5,
    game = 6
};

/**
 * The unique message ID of the message.
 * See the STORM 2027 Serial Specification for which messages carry what data
 */
enum Message {
    ComputerRequest = 10,
    Heartbeat = 11,
    Configuration = 12,
    ConfigComplete = 13,
    RobotVelocity = 20,
    DriveVelocity = 21,
    DriveVoltage = 22,
    DriveRaw = 23,
    DriveFeedback = 24,
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
typedef struct HeartbeatMsg {
    char b = 0xFF; //TODO FIXME
} HeartbeatMsg;

// ID 12
typedef struct ConfigurationMsg {
    uint8_t type;
    uint8_t ID;
    //TODO
} ConfigurationMsg;

// ID 13
typedef struct ConfigCompleteMsg {
    char b = 0x00;
} ConfigCompleteMsg;

// ID 20
typedef struct RobotVelocityCmd {
    int16_t forward_velocity;
    int16_t sideways_velocity;
    int16_t rotational_velocity;
} RobotVelocityCmd;

// ID 21
typedef struct DriveVelocityCmd {
    int16_t front_left_velocity;
    int16_t front_right_velocity;
    int16_t back_left_velocity;
    int16_t back_right_velocity;
} DriveVelocityCmd;

// ID 22
typedef struct DriveVoltageCmd {
    int16_t front_left_voltage;
    int16_t front_right_voltage;
    int16_t back_left_voltage;
    int16_t back_right_voltage;
} DriveVoltageCmd;

// ID 23
typedef struct DriveRawCmd {
    int16_t front_left_raw;
    int16_t front_right_raw;
    int16_t back_left_raw;
    int16_t back_right_raw;
} DriveRawCmd;

// ID 24
typedef struct DriveFeedbackRsp {
    int16_t forward_velocity;
    int16_t sideways_velocity;
    int16_t rotational_velocity;
    int16_t delta_x;
    int16_t delta_y;
    int16_t delta_theta;
} DriveFeedbackRsp;

// ID 25
typedef struct BatteryVoltageRsp {
    uint8_t voltage;
} BatteryVoltageRsp;

// ID 30
typedef struct TaskCommandCmd {
    //FIXME - message not defined yet
    int16_t intake_velocity;
    uint8_t arm_position;
    uint16_t climber_position;
    uint8_t charging_wheel_velocity;
} TaskCommandCmd;

// ID 31
typedef struct TaskResponseRsp {
    //FIXME - message not defined yet
    int16_t intake_velocity;
    uint8_t arm_position;
    uint16_t climber_position;
    uint8_t charging_wheel_velocity;
} TaskResponseRsp;

// ID 40
typedef struct SensorResponseRsp {
    //FIXME - message not defined yet
    int8_t robot_current;
    uint16_t arm_distance;
    uint16_t back_distance;
    bool intake_possession;
} SensorResponseRsp;

// ID 50
typedef struct ServoCommandCmd {
    //FIXME - message not defined yet
    uint8_t arm_position;
    int8_t wrist_position;
    bool claw_toggle;
    //TODO: other servos here
} ServoCommandCmd;

// ID 60
typedef struct GameCommandCmd {
    //FIXME - message not defined yet
    char TEMPORARY;
} GameCommandCmd;

// ID 61
typedef struct GameResponseRsp {
    //FIXME - message not defined yet
    char TEMPORARY;
} GameResponseRsp;

// ================================================

class StormMessage {
public:
    Message type;
    Address address;
    uint8_t size;
    char DATA[16];

    StormMessage(Message type, Address address, uint8_t size, char* data) {
        this->type = type;
        this->address = address;
        this->size = size;
        
        for (uint8_t i = 0; i < size; i++) {
            DATA[i] = data[i];
        }
    }

    ~StormMessage() {
        //TODO
    }

    // message conversion methods
    Request AsRequest() {
        Request msg;

        return msg; 
    }

    HeartbeatMsg AsHeartbeat() {
        HeartbeatMsg msg;

        //TODO

        return msg;
    }

    ConfigurationMsg AsConfiguration() {
        ConfigurationMsg msg;

        //TODO

        return msg;
    }

    ConfigCompleteMsg AsConfigurationComplete() {
        ConfigCompleteMsg msg;

        //TODO

        return msg;
    }

    RobotVelocityCmd AsRobotVelocity() {
        RobotVelocityCmd cmd;

        //TODO

        return cmd;
    }

    DriveVelocityCmd AsDriveVelocity() {
        DriveVelocityCmd cmd;

        //TODO

        return cmd;
    }

    DriveVoltageCmd AsDriveVoltage() {
        DriveVoltageCmd cmd;

        //TODO

        return cmd;
    }

    DriveRawCmd AsDriveRaw() {
        DriveRawCmd cmd;

        //TODO

        return cmd;
    }

    DriveFeedbackRsp AsDriveFeedback() {
        DriveFeedbackRsp rsp;

        //TODO

        return rsp;
    }

    BatteryVoltageRsp AsBatteryVoltage() {
        BatteryVoltageRsp rsp;
        
        //TODO

        return rsp;
    }

    TaskCommandCmd AsTaskCommand() {
        TaskCommandCmd cmd;
        
        //TODO

        return cmd;
    }

    TaskResponseRsp AsTaskResponse() {
        TaskResponseRsp rsp;

        //TODO

        return rsp;
    }

    SensorResponseRsp AsSensorResponse() {
        SensorResponseRsp rsp;
        
        //TODO

        return rsp;
    }

    ServoCommandCmd AsServoCommand() {
        ServoCommandCmd cmd;
        
        //TODO

        return cmd;
    }

    GameCommandCmd AsGameCommand() {
        GameCommandCmd cmd;
        
        //TODO

        return cmd;
    }

    GameResponseRsp AsGameResponse() {
        GameResponseRsp rsp;
        
        //TODO

        return rsp;
    }
};