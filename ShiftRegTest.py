from pymata4 import pymata4
import time

DATA_PIN  = 11
CLOCK_PIN = 12
LATCH_PIN = 8

board = pymata4.Pymata4()
time.sleep(2)

board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)

def shift_out(value, msb_first=True):
    board.digital_write(LATCH_PIN, 0)
    bit_range = range(7, -1, -1) if msb_first else range(8)
    for i in bit_range:
        bit = (value >> i) & 1
        board.digital_write(DATA_PIN, bit)
        board.digital_write(CLOCK_PIN, 1)
        board.digital_write(CLOCK_PIN, 0)
    board.digital_write(LATCH_PIN, 1)

# Keeps track of which LEDs are currently on
current_state = 0b00000000

def set_led(index, on):
    """
    Turn a single LED on or off, without changing the others.
    index: 0-7, which LED to control
    on: True to turn on, False to turn off
    """
    global current_state

    if on:
        current_state |= (1 << index)   # set that bit to 1
    else:
        current_state &= ~(1 << index)  # clear that bit to 0

    shift_out(current_state)

set_led(3, True)   # turn on LED 3, leave everything else as-is
time.sleep(0.01)
set_led(5, True)   # turn on LED 5 too — LED 3 stays on
time.sleep(0.01)
set_led(3, False)  # turn off LED 3 — LED 5 stays on
time.sleep(0.01)
set_led(5, False)  # turn off LED 5 — all off now
time.sleep(0.01)

board.shutdown()