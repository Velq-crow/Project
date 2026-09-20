# Subsystem 4 Eng1013
# Created Date:6/9/26
# Created By: Ketan
# Version: 1.3

from pymata4 import pymata4
import time

board = pymata4.Pymata4()

# Constants
TOP_HEIGHT = 10 #cm
pollingRate  = 0.5   # seconds
overHeightLimit = 4

DATA_PIN  = 12
CLOCK_PIN = 13
LATCH_PIN = 11

BUZZER_PA1 = 0x80  # Pin 1
GREEN_TL1  = 0x40  # Pin 2
GREEN_TL2  = 0x20  # Pin 3
YELLOW_TL1 = 0x10  # Pin 4
YELLOW_TL2 = 0x08  # Pin 5
RED_TL1    = 0x04  # Pin 6
RED_TL2    = 0x02  # Pin 7
LIGHTS_WL1 = 0x01  # Pin 8

TL1_MASK = GREEN_TL1 | YELLOW_TL1 | RED_TL1
TL2_MASK = GREEN_TL2 | YELLOW_TL2 | RED_TL2
PA1_MASK = BUZZER_PA1
WL1_MASK = LIGHTS_WL1

_chip1_state = 0x00

overheight = {
    "us1": False, "us2": False,
    "us3": False, "us4": False,
    "us5": False,
}

ss1_was_overridden = False

# US1 & TL1
echoPinUS1    = 3
triggerPinUS1 = 4
ss1_TL1_phase = "green"   # red, green, yellow
ss1_TL1_phase_start = 0.0

# US2
echoPinUS2    = 3
triggerPinUS2 = 4
ss1_TL2_phase = "green"   # red, green, yellow
ss1_TL2_phase_start = 0.0

board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)


board.set_pin_mode_sonar(triggerPinUS1, echoPinUS1, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS2, echoPinUS2, timeout=200000)


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

def set_shift1(mask, bits_on):
    global _chip1_state
    _chip1_state = (_chip1_state & ~mask) | (bits_on & mask)
    update_3_chips(_chip1_state, 0x00, 0x00)

def heightDiff(distance):
    """
    Used to minus the distance measured by the ultrasonic sensor (US5) from the TOP_HEIGHT to give actual height of the vechicle.

        Parameters:
            distance: To be used in calculation TOP_HEIGHT - distance[]

        Returns:
            Returns TOP_HEIGHT - distance[0]
    """
    return TOP_HEIGHT - distance[0]

def normal_state_ss1_TL1():
    set_shift1(TL1_MASK,GREEN_TL1)

def normal_state_ss1_TL2():
    set_shift1(TL2_MASK,GREEN_TL2)

def yellow_state_ss1_TL1():
    set_shift1(TL1_MASK,YELLOW_TL1)

def yellow_state_ss1_TL2():
    set_shift1(TL2_MASK,YELLOW_TL2)

def overheight_state_ss1_TL1():
    set_shift1(TL1_MASK,RED_TL1)

def overheight_state_ss1_TL2():
    set_shift1(TL2_MASK,RED_TL2)

def enter_override():
    set_shift1(TL1_MASK | TL2_MASK | PA1_MASK | WL1_MASK, RED_TL1 | RED_TL2 | BUZZER_PA1 | LIGHTS_WL1)

def exit_override():
    # PA1/WL1 bits are in mask but not in bits_on -> cleared
    set_shift1(TL1_MASK | TL2_MASK | PA1_MASK | WL1_MASK, GREEN_TL1 | GREEN_TL2)


def ss1_step(now, is_overheight_US1, is_overheight_US2):
    global ss1_TL1_phase, ss1_TL1_phase_start, ss1_TL2_phase, ss1_TL2_phase_start
    global ss1_was_overridden

    override = overheight["us3"] and overheight["us4"]

    if override:
        if not ss1_was_overridden:
            enter_override()
            ss1_TL1_phase, ss1_TL1_phase_start = "red", now
            ss1_TL2_phase, ss1_TL2_phase_start = "red", now
            ss1_was_overridden = True
        return

    if ss1_was_overridden:
        exit_override()
        ss1_TL1_phase, ss1_TL1_phase_start = "green", now
        ss1_TL2_phase, ss1_TL2_phase_start = "green", now
        ss1_was_overridden = False

    # --- 1.R2: TL1 driven by US1 ---
    if ss1_TL1_phase == "green":
        if is_overheight_US1:
            yellow_state_ss1_TL1()
            ss1_TL1_phase, ss1_TL1_phase_start = "yellow", now

    elif ss1_TL1_phase == "yellow":
        if now - ss1_TL1_phase_start >= 1:
            overheight_state_ss1_TL1()
            ss1_TL1_phase, ss1_TL1_phase_start = "red", now

    elif ss1_TL1_phase == "red":
        if now - ss1_TL1_phase_start >= 30:
            normal_state_ss1_TL1()
            ss1_TL1_phase = "green"

    if ss1_TL2_phase == "green":
        if is_overheight_US2 and ss1_TL1_phase == "green":

            yellow_state_ss1_TL1()
            ss1_TL1_phase, ss1_TL1_phase_start = "yellow", now

            yellow_state_ss1_TL2()
            ss1_TL2_phase, ss1_TL2_phase_start = "yellow", now

        elif is_overheight_US2 and ss1_TL1_phase != "green":
            yellow_state_ss1_TL2()
            ss1_TL2_phase, ss1_TL2_phase_start = "yellow", now

    elif ss1_TL2_phase == "yellow":
        if now - ss1_TL2_phase_start >= 1:
            overheight_state_ss1_TL2()
            ss1_TL2_phase, ss1_TL2_phase_start = "red", now

    elif ss1_TL2_phase == "red":
        if now - ss1_TL2_phase_start >= 30:
            normal_state_ss1_TL2()
            ss1_TL2_phase = "green"

    
        


def main():
    time.sleep(1)
    while True:
        try: 
            lastPollTime = time.time()
            while True:
                currentTime = time.time()
                if (currentTime - lastPollTime) >= pollingRate:
                    lastPollTime = currentTime

                    # reads & calcuations
                    heightUS1 = heightDiff(board.sonar_read(triggerPinUS1)) # height of veh from us3 - ss4
                    heightUS2 = heightDiff(board.sonar_read(triggerPinUS2)) # height of veh from us4 - ss4

                    overheight["us1"] = heightUS1 >= overHeightLimit
                    overheight["us2"] = heightUS2 >= overHeightLimit

                    normal_state_ss1_TL1()
                    normal_state_ss1_TL2()

                    ss1_step(currentTime,overheight["us1"],overheight["us2"])
                    
        except KeyboardInterrupt:
            update_3_chips(0x00, 0x00, 0x00)
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()