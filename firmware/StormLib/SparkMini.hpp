#pragma once

// CONSTANTS (non-configurable)
const unsigned int full_reverse = 500; // micros
const unsigned int neutral = 1500; // micros
const unsigned int forward = 2500; // micros
const unsigned int input_freq = 100; // Hz
const unsigned int watchdog_timeout = 65; // ms

// PWM frequency calculated from page 1084 of the RP2350 datasheet:
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
// which is alright I guess. note this is WITHOUT phase correct set, so we need to set a divider of 3.


/**
 * TODO: write a bunch of documentation n stuff
 * also note most functions return a bool, if false something bad happened and you should show it via debug LED
 */
class SparkMini {
public:
    /**
     * TODO: document this
     */
    SparkMini(unsigned int OUTPUT_PIN) {
        this->out_pin = OUTPUT_PIN;

        this->has_encoder = false;

        this->initialized = false;
    }

    /**
     * TODO: document this
     */
    SparkMini(unsigned int OUTPUT_PIN, unsigned int ENC_A_PIN, unsigned int ENC_B_PIN) {
        this->out_pin = OUTPUT_PIN;
        this->enc_a_pin = ENC_A_PIN;
        this->enc_b_pin = ENC_B_PIN;

        this->has_encoder = true;

        this->initialized = false;
    }

    ~SparkMini();

    /**
     * TODO: document this
     */
    bool Init() {
        // pin modes

        //TODO: set each GPIO function (Section 9.4, page 589)
        //TODO: also configure the pads (section 9.6, page 595)

        pinMode(this->out_pin, OUTPUT);
        pinMode(this->enc_a_pin, INPUT);
        pinMode(this->enc_b_pin, INPUT);

        // PWM configuration
        //FIXME: do like, the actual PWM with the TOP register and clock divider and everything
        analogWriteResolution(8);
        analogWriteFreq(333); // this is what worked last year

        // PIO setup
        //TODO: figure this out. likely copy this repo: https://github.com/pmarques-dev/PicoEncoder
        //TODO: attach encoder interrupts

        this->lastCmdTime = 0;

        this->initialized = true;

        return this->initialized;
    }

    /**
     * TODO: document this
     */
    bool Stop() {
        this->initialized = false;
        this->lastCmdTime = 999999999;

        // depower the actuators
        digitalWrite(this->out_pin, LOW);

        // detach encoder interrupts
        //TODO
    }

    /**
     * TODO: document this
     */
    bool UpdateEncoder() {
        //TODO
    }

    /**
     * TODO: document this
     */
    bool SetRaw(int16_t raw_output) {
        float16_t scaled = raw_output / MAX_INT16;

        uint8_t output = 255 * scaled;

        //TODO FIXME: make this like, the actual PWM stuff
        analogWrite(this->out_pin, output);

        return true;
    }

    /**
     * TODO: document this
     */
    bool SetVelocity(int16_t velocity) {
        // TODO
    }

    /**
     * TODO: document this
     */
    bool SetVoltage(uint8_t voltage, uint8_t battVoltage) {
        // TODO: figure out what output corresponds to what voltage on the output or somethin
        // for now, assume MAX_UINT8_T is 12 volts
    }

private:
    //TODO: whenever we do pins check if they are 0 and disallow if so
    unsigned int out_pin = 0;
    unsigned int enc_a_pin = 0;
    unsigned int enc_b_pin = 0;
    bool has_encoder = false;

    bool initialized = false;
    unsigned long lastCmdTime = 0;
};