#pragma once

#include <stdlib.h>
#include "SparkMini.hpp"

// TODO

class MecanumDrive {
public:
    /**
     * TODO: document
     */
    MecanumDrive(std::shared_ptr<SparkMini> fl_motor, std::shared_ptr<SparkMini> fr_motor, std::shared_ptr<SparkMini> bl_motor, std::shared_ptr<SparkMini> br_motor) {
        this->fl_motor = fl_motor;
        this->fr_motor = fr_motor;
        this->bl_motor = bl_motor;
        this->br_motor = br_motor;
    }

    /**
     * TODO: document
     */
    ~MecanumDrive() {
        // TODO
    }

    /**
     * TODO: document
     */
    bool Init() {
        // re-initialize all motors
        this->fl_motor->Init();
        this->fr_motor->Init();
        this->bl_motor->Init();
        this->br_motor->Init();

        // reset odometry
        this->heading = 0.0f;

        // reset safety
        this->MotionAllowed = false;

        return true;
    }

    // periodic function (call this every loop/tick)
    /**
     * TODO: document
     */
    void Periodic() {
        //TODO
    }

    // === setters ===
    /**
     * TODO: document
     */
    void SetMotionAllowed(bool MotionAllowed) {
        this->MotionAllowed = MotionAllowed;
    }

    //TODO: set scaler values?
    // ===============

    // === drive functions ===
    /**
     * TODO: document
     */
    void SetVelocity(float forward_velocity, float sideways_velocity, float rotational_velocity, bool field_oriented = false) {
        float fl_vel, fr_vel, bl_vel, br_vel;
        
        //TODO

        if (field_oriented) {
            //TODO: not implemented yet
        }

        if (this->MotionAllowed) {
            this->fl_motor->SetVelocity(fl_vel);
            this->fr_motor->SetVelocity(fr_vel);
            this->bl_motor->SetVelocity(bl_vel);
            this->br_motor->SetVelocity(br_vel);
        }

        return;
    }

    /**
     * TODO: document
     */
    void SetMotorVelocities(float fl_vel, float fr_vel, float bl_vel, float br_vel) {
        if (this->MotionAllowed) {
            this->fl_motor->SetVelocity(fl_vel);
            this->fr_motor->SetVelocity(fr_vel);
            this->bl_motor->SetVelocity(bl_vel);
            this->br_motor->SetVelocity(br_vel);
        }
    }

    /**
     * TODO: document
     */
    void SetMotorVoltages(float fl_voltage, float fr_voltage, float bl_voltage, float br_voltage, float batt_voltage = 12.0f) {
        if (this->MotionAllowed) {
            this->fl_motor->SetVelocity(fl_voltage, batt_voltage);
            this->fr_motor->SetVelocity(fr_voltage, batt_voltage);
            this->bl_motor->SetVelocity(bl_voltage, batt_voltage);
            this->br_motor->SetVelocity(br_voltage, batt_voltage);
        }
    }

    /**
     * TODO: document
     */
    void SetMotorRaw(float fl_raw, float fr_raw, float bl_raw, float br_raw) {
        if (this->MotionAllowed) {
            this->fl_motor->SetRaw(fl_raw);
            this->fr_motor->SetRaw(fr_raw);
            this->bl_motor->SetRaw(bl_raw);
            this->br_motor->SetRaw(br_raw);
        }
    }
    // =======================

private:
    // motor objects
    std::shared_ptr<SparkMini> fl_motor;
    std::shared_ptr<SparkMini> fr_motor;
    std::shared_ptr<SparkMini> bl_motor;
    std::shared_ptr<SparkMini> br_motor;

    // field-oriented
    float32_t heading = 0.0f; //FIXME assume we start with 0 heading

    bool MotionAllowed = false;
};