#pragma once

// CONSTANTS (non-configurable)
const unsigned int full_reverse = 500; // micros
const unsigned int neutral = 1500; // micros
const unsigned int forward = 2500; // micros
const unsigned int input_freq = 100; // Hz
const unsigned int watchdog_timeout = 65.5; // ms

// PWM frequency calculated from page 1084 of the RP2350 datasheet

// if we set phase-correct mode we can halve the output frequency

// TOP can range from 0 to 65_536
// we need the period to range from ~400 to ~2600 us
// period (in # clock cycles) = (top + 1) * (phase_correct? + 1) * (div_int + div_frac/16)
// freq_pwm = freq_sys / period
// we want freq_pwm to be 50-200 Hz, so roughly 150 Hz
// with a 150 MHz system clock speed, each clock cycle is ~6.67 nanoseconds
// the minimum period needs to thus be 59970 cycles,
// and the maximum period is 389805
// that is obviously too much, and to fit it into TOP we need to divide it by like, 5.947
// so a clock divider of 6? which gives us a frequency of 381.5 Hz at maximum TOP value
// which is alright I guess. note this is WITHOUT phase correct set.

/**
 * TODO: write a bunch of documentation n stuff
 */
class SparkMini {
public:
    SparkMini(unsigned int OUTPUT_PIN) {
        this->out_pin = OUTPUT_PIN;

        this->has_encoder = false;
    }

    SparkMini(unsigned int OUTPUT_PIN, unsigned int ENC_A_PIN, unsigned int ENC_B_PIN) {
        this->out_pin = OUTPUT_PIN;
        this->enc_a_pin = ENC_A_PIN;
        this->enc_b_pin = ENC_B_PIN;

        this->has_encoder = true;
    }

    ~SparkMini();

    void Init() {
        //TODO: initalization n stuf I guess

        // pin mode
        // PWM configuration
        // PIO setup

        this->initialized = true;
    }

    //TODO: do we want to do something like a MotorSafety or EStoppable interface like WPILib?
    void Depower() {
        // TODO
    }

    void SetRaw(int16_t raw_output) {
        // TODO
    }

    void SetVelocity() {
        // TODO
    }

    void SetVoltage() {
        // TODO: figure out what output corresponds to what voltage on the output or somethin
    }
private:
    //TODO: whenever we do pins check if they are 0 and disallow if so
    unsigned int out_pin = 0;
    unsigned int enc_a_pin = 0;
    unsigned int enc_b_pin = 0;
    bool has_encoder = false;

    bool initialized = false;
};