#pragma once


class QuadratureEncoder : () {
public:
    QuadratureEncoder() {
        //TODO

        if (use_pio) {
            SetupPIO();
        } else {
            SetupInterrupts();
        }
    }

    //TODO: destructor

    void SetupInterrupts() {

    }

    void SetupPIO() {
        //TODO
    }

    float GetRotations() {
        //TODO
    }

    //TODO: include anything else in this class?

private:
    // default pins, TODO: include guard wherever used
    uint8_t m_pinA = 255;
    uint8_t m_pinB = 255;

    // if enabled, uses the Pico 2's PIO to measure encoder pulses
    // if NOT enabled, just uses interrupts
    bool use_pio = false;
}