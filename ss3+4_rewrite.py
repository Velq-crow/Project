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

DATA_PIN  = 12
CLOCK_PIN = 13
LATCH_PIN = 11


# Bit layout (single 8-bit register, shared by TL6 and TL3)
TL6_RED    = 0x80
TL6_YELLOW = 0x40
TL6_GREEN  = 0x20
TL3_RED    = 0x10
TL3_GREEN  = 0x08

TL6_MASK = TL6_RED | TL6_YELLOW | TL6_GREEN
TL3_MASK = TL3_RED | TL3_GREEN

chip3_state = 0x00

overheight = {
    "us1": False, "us2": False,
    "us3": False, "us4": False,
    "us5": False,
}

# US5 (TL6 / ss3)
echoPinUS5    = 3
triggerPinUS5 = 4
us5_was_overheight = False
us5_just_exited = False
ss3_phase = "normal"   # normal, green, yellow
ss3_phase_start = 0.0

# US3 / US4 (TL3 / ss4)
triggerPinUS3 = 9
echoPinUS3    = 6
triggerPinUS4 = 8
echoPinUS4    = 7
acceptableError = 10  # percent
ss4_phase = "normal"


board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)


board.set_pin_mode_sonar(triggerPinUS5, echoPinUS5, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS3, echoPinUS3, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS4, echoPinUS4, timeout=200000)

time.sleep(1)

def any_overheight():
    return any(overheight.values())

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

def set_shift3(mask, bits_on):
    global _chip3_state
    _chip3_state = (_chip3_state & ~mask) | (bits_on & mask)
    update_3_chips(0x00, 0x00, _chip3_state)

def heightDiff(distance):
    """
    Used to minus the distance measured by the ultrasonic sensor (US5) from the TOP_HEIGHT to give actual height of the vechicle.

        Parameters:
            distance: To be used in calculation TOP_HEIGHT - distance[]

        Returns:
            Returns TOP_HEIGHT - distance[0]
    """
    return TOP_HEIGHT - distance[0]

def overheight_state_ss4():
    set_shift3(TL3_MASK, TL3_RED)

def normal_state_ss4():
    set_shift3(TL3_MASK, TL3_GREEN)

def normal_state_ss3():
    set_shift3(TL6_MASK, TL6_RED)

def overheight_state_ss3():
    set_shift3(TL6_MASK, TL6_GREEN)

def yellow_state_ss3():
    set_shift3(TL6_MASK, TL6_YELLOW)

def ss3_step(now, is_overheight):
    global ss3_phase, ss3_phase_start

    if ss3_phase == "normal":
        if is_overheight:
            overheight_state_ss3()
            ss3_phase, ss3_phase_start = "green", now

    elif ss3_phase == "green":
        if now - ss3_phase_start >= 5: #time green
            yellow_state_ss3()
            ss3_phase, ss3_phase_start = "yellow", now

    elif ss3_phase == "yellow": # time yellow
        if now - ss3_phase_start >= 3:
            normal_state_ss3()
            ss3_phase = "normal"

def ss4_step (is_overheight, us5_just_exited):
    global ss4_phase
    if ss4_phase == "normal":
        if is_overheight:
            overheight_state_ss4()
            ss4_phase = "overheight"
    elif ss4_phase == "overheight":
        if us5_just_exited and not any_overheight():
            normal_state_ss4()
            ss4_phase = "normal"

def main():
    while True:
        try: 
            #Validation loop
            overHeightLimit = None
            while overHeightLimit is None or overHeightLimit < 0 or overHeightLimit > TOP_HEIGHT:
                limitInput = input("Enter the height limit (m): ").strip()
                try:
                    if overHeightLimit == "":
                        print("Assigning default height")
                        overHeightLimit = 4
                        break

                    overHeightLimit = int(limitInput)

                    if overHeightLimit < 0:
                        print("Invalid input. height limit cannot be negative.")
                        overHeightLimit = None

                    if overHeightLimit > TOP_HEIGHT:
                        print(f"Invalid input. height limit cannot be more than {TOP_HEIGHT}.")
                        overHeightLimit = None
                except ValueError:
                    print("Invalid input. Please enter a whole number.")

            normal_state_ss3()
            normal_state_ss4()


            lastPollTime = time.time()
            while True:
                currentTime = time.time()
                if (currentTime - lastPollTime) >= pollingRate:
                    lastPollTime = currentTime


                    # reads & calcuations
                    heightUS3 = heightDiff(board.sonar_read(triggerPinUS3)) # height of veh from us3 - ss4
                    heightUS4 = heightDiff(board.sonar_read(triggerPinUS4)) # height of veh from us4 - ss4
                    heightUS5 = heightDiff(board.sonar_read(triggerPinUS5)) # height of veh from us5 - ss3
                    
                    lowerErrorBound = heightUS3*(1- acceptableError/100)
                    upperErrorBound = heightUS3*(1+ acceptableError/100)

                    overheight["us3"] = heightUS3 >= overHeightLimit
                    overheight["us4"] = heightUS4 >= overHeightLimit
                    overheight["us5"] = heightUS5 >= overHeightLimit

                    us5_just_exited = us5_was_overheight and not overheight["us5"]
                    us5_was_overheight = overheight["us5"]
                    
                    print(f"US3 height: {heightUS3:.2f} cm \n US4 height: {heightUS4:.2f} cm \n US5 height: {heightUS5:.2f} cm")
                    # execution & logic
                    is_over_ss4 = overheight["us3"] and lowerErrorBound <= heightUS4 <= upperErrorBound

                    #ss4 logic
                    ss4_step(is_over_ss4,us5_just_exited)
                    #ss3 logic
                    ss3_step(currentTime,overheight["us5"])

        except KeyboardInterrupt:
            update_3_chips(0x00, 0x00, 0x00)
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()