#pragma once

// TODO

class MecanumDrive {
public:
    MecanumDrive() {
        // TODO: pass motor objects in?
    }

    ~MecanumDrive() {
        // TODO
    }

    bool Init() {
        //TODO

        return true;
    }

    // periodic function (call this every loop/tick)
    void Periodic() {
        //TODO
    }

    // === setters ===
    void SetMotionAllowed(bool MotionAllowed) {
        this->MotionAllowed = MotionAllowed;
    }

    //TODO: set scaler values?
    // ===============

    // === drive functions ===
    void SetVelocity(float forward_velocity, float sideways_velocity, float rotational_velocity) {
        // TODO
    }

    void SetMotorVelocities(float fl_vel, float fr_vel, float bl_vel, float br_vel) {
        // TODO
    }

    void SetMotorVoltages(float fl_voltage, float fr_voltage, float bl_voltage, float br_voltage) {
        // TODO
    }

    void SetMotorRaw(float fl_raw, float fr_raw, float bl_raw, float br_raw) {
        // TODO
    }
    // =======================

private:
    //TODO: pins and things

    bool MotionAllowed = false;
};