from pymata4 import pymata4
import time

DATA_PIN  = 11
CLOCK_PIN = 12
LATCH_PIN = 8

from pymata4 import pymata4
import time

board = pymata4.Pymata4()

board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)

time.sleep(1)

def shift_out(value, num_bits=8, msb_first=True):
    board.digital_write(LATCH_PIN, 0)
    bit_range = range(num_bits - 1, -1, -1) if msb_first else range(num_bits)
    for i in bit_range:
        bit = (value >> i) & 1
        board.digital_write(DATA_PIN, bit)
        board.digital_write(CLOCK_PIN, 1)
        board.digital_write(CLOCK_PIN, 0)
    board.digital_write(LATCH_PIN, 1)

def update_3_chips(chip3_val, chip2_val, chip1_val):
    combined = (chip3_val << 16) | (chip2_val << 8) | chip1_val
    shift_out(combined, num_bits=24)

def test_all_leds():
    # Flash each of the 24 LEDs one at a time
    for n in range(24):
        value = 1 << n
        chip1_val = value & 0xFF
        chip2_val = (value >> 8) & 0xFF
        chip3_val = (value >> 16) & 0xFF
        update_3_chips(chip3_val, chip2_val, chip1_val)
        time.sleep(0.2)
        update_3_chips(0x00, 0x00, 0x00)  # off before next LED
        time.sleep(0.1)

    # All LEDs on
    update_3_chips(0xFF, 0xFF, 0xFF)
    time.sleep(1)

    # All LEDs off
    update_3_chips(0x00, 0x00, 0x00)

def main():
    while True:
        try: 
            test_all_leds()
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()



