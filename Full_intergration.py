# Subsystem 4 Eng1013
# Created Date:6/9/26
# Created By: Ketan
# Version: 1.3


from pymata4 import pymata4
import time

board = pymata4.Pymata4()

# Constants
TOP_HEIGHT = 10 #cm
pollingRate  = 0.1   # seconds
calibrated_value_day = 250

DATA_PIN  = 13
CLOCK_PIN = 11
LATCH_PIN = 12


#SS3 AND 4
RED_TL6    = 0x08
GREEN_TL3  = 0x40
GREEN_TL6  = 0x20
YELLOW_TL6 = 0x10
RED_TL3    = 0x01

#SS 2
RED_TL5    = 0x80  # Pin 8
RED_TL4    = 0x40  # Pin 7
YELLOW_TL5 = 0x20  # Pin 6
YELLOW_TL4 = 0x10  # Pin 5
GREEN_TL5  = 0x08  # Pin 4
GREEN_TL4  = 0x04  # Pin 3
RED_PED    = 0x02  # Pin 2
GREEN_PED  = 0x01  # Pin 1

#SS 1
BUZZER_PA1 = 0x80  # Pin 1
GREEN_TL1  = 0x40  # Pin 2
GREEN_TL2  = 0x20  # Pin 3
YELLOW_TL1 = 0x10  # Pin 4
YELLOW_TL2 = 0x08  # Pin 5
RED_TL1    = 0x04  # Pin 6
RED_TL2    = 0x02  # Pin 7
LIGHTS_WL1 = 0x01  # Pin 8

TL6_MASK = RED_TL6 | YELLOW_TL6 | GREEN_TL6
TL5_MASK = RED_TL5 | YELLOW_TL5 | GREEN_TL5
TL4_MASK = RED_TL4 | YELLOW_TL4 | GREEN_TL4
TL3_MASK = RED_TL3 | GREEN_TL3
TL2_MASK = GREEN_TL2 | YELLOW_TL2 | RED_TL2
TL1_MASK = GREEN_TL1 | YELLOW_TL1 | RED_TL1
PED_MASK = RED_PED | GREEN_PED
PA1_MASK = BUZZER_PA1
WL1_MASK = LIGHTS_WL1

chip3_state = 0x00
chip2_state = 0x00
chip1_state = 0x00


overheight = {
    "us1": False, "us2": False,
    "us3": False, "us4": False,
    "us5": False,
}

ldr_reading = {
    "ldr_DS1": True,
    "ldr_DS2": True
}

# US5 (TL6 / ss3)
echoPinUS5    = 2
triggerPinUS5 = 3
us5_was_overheight = False
us5_just_exited = False
ss3_phase = "normal"   # normal, green, yellow
ss3_phase_start = 0.0

# US3 / US4 (TL3 / ss4)
triggerPinUS3 = 4
echoPinUS3    = 5
triggerPinUS4 = 8
echoPinUS4    = 9
acceptableError = 10  # percent
ss4_phase = "normal"
# SS2
ss2_state = "TL4_GREEN"
ss2_state_start = 0.0
ss2_ped_requested = False
ss2_flash_state = False
ss2_flash_last_toggle = 0.0
ss3_hold_active = False
ss3_hold_start = 0.0
ss2_hold_requested = False


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
ss1_was_overridden = False

ldrPinDS1 = 0
ldrPinDS2 = 1
pedestrianButton=2

GREEN = True
RED = False



board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)

board.set_pin_mode_digital_input_pullup(pedestrianButton)


board.set_pin_mode_sonar(triggerPinUS5, echoPinUS5, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS3, echoPinUS3, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS4, echoPinUS4, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS1, echoPinUS1, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS2, echoPinUS2, timeout=200000)
board.set_pin_mode_analog_input(ldrPinDS1)
board.set_pin_mode_analog_input(ldrPinDS2)


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
    global chip3_state
    chip3_state = (chip3_state & ~mask) | (bits_on & mask)
    update_3_chips(chip1_state, chip3_state, chip2_state )

def set_shift2(mask, bits_on):
    global chip2_state
    chip2_state = (chip2_state & ~mask) | (bits_on & mask)
    update_3_chips(chip1_state, chip3_state, chip2_state )

def set_shift1(mask, bits_on):
    global chip1_state
    chip1_state = (chip1_state & ~mask) | (bits_on & mask)
    update_3_chips(chip1_state, chip3_state, chip2_state)

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
    set_shift3(TL3_MASK, RED_TL3)

def normal_state_ss4():
    set_shift3(TL3_MASK, GREEN_TL3)

def normal_state_ss3():
    set_shift3(TL6_MASK, RED_TL6)

def overheight_state_ss3():
    set_shift3(TL6_MASK, GREEN_TL6)

def yellow_state_ss3():
    set_shift3(TL6_MASK, YELLOW_TL6)

def tl4_cycle_state():
    set_shift2(TL4_MASK, GREEN_TL4)

def tl4_cycle_state_off():
    set_shift2(TL4_MASK, YELLOW_TL4)

def tl5_cycle_state():
    set_shift2(TL5_MASK, GREEN_TL5)

def tl5_cycle_state_off():
    set_shift2(TL5_MASK, YELLOW_TL5)

def cycle_state_pedestrian(state):
    if state == GREEN:
        set_shift2(PED_MASK | TL4_MASK | TL5_MASK, GREEN_PED | RED_TL4 | RED_TL5)
    else:
        set_shift2(PED_MASK, RED_PED)

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

def ss1_step(now):
    global ss1_TL1_phase, ss1_TL1_phase_start, ss1_TL2_phase, ss1_TL2_phase_start
    global ss1_was_overridden

    override = overheight["us3"] and overheight["us4"]
    is_overheight_US1 = overheight["us1"]
    is_overheight_US2 = overheight["us2"]
    
    if is_overheight_US1:
        print(board.sonar_read(triggerPinUS1))
    
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

def ss2_step(now):
    global ss2_state, ss2_state_start, ss2_ped_requested
    global ss2_flash_state, ss2_flash_last_toggle

    is_day = ldr_reading["ldr_DS2"]
    elapsed = now - ss2_state_start
    tl4_green_time = 20 if is_day else 30
    tl5_green_time = 10 if is_day else 5

    if ss2_state in ("TL4_GREEN", "TL5_GREEN", "TL4_YELLOW", "TL5_YELLOW"):
        if board.digital_read(pedestrianButton)[0] == 0:
            print("button pressed")
            ss2_ped_requested = True
 
    if ss2_state == "TL4_GREEN":
        tl4_cycle_state()
        if ss2_ped_requested:
            tl4_cycle_state_off()
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif ss2_hold_requested:
            tl4_cycle_state_off()
            ss2_state, ss2_state_start = "TL4_YELLOW", now
        elif elapsed > tl4_green_time:
            tl4_cycle_state_off()
            ss2_state, ss2_state_start = "TL4_YELLOW", now
 
    elif ss2_state == "TL4_YELLOW":
        if ss2_ped_requested:
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif elapsed > 3:
            if ss2_hold_requested:
                cycle_state_pedestrian(GREEN)
                ss2_state, ss2_state_start = "TL_HOLD", now
            else:
                ss2_state, ss2_state_start = "TL5_GREEN", now
 
    elif ss2_state == "TL5_GREEN":
        tl5_cycle_state()
        if ss2_ped_requested:
            tl5_cycle_state_off()
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif ss2_hold_requested:
            tl5_cycle_state_off()
            ss2_state, ss2_state_start = "TL5_YELLOW", now
        elif elapsed > tl5_green_time:
            tl5_cycle_state_off()
            ss2_state, ss2_state_start = "TL5_YELLOW", now

    elif ss2_state == "TL5_YELLOW":
        if ss2_ped_requested:
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif elapsed > 3:
            if ss2_hold_requested:
                cycle_state_pedestrian(GREEN)
                ss2_state, ss2_state_start = "TL_HOLD", now
            else:
                ss2_state, ss2_state_start = "TL4_GREEN", now
 
    elif ss2_state == "PED_YELLOW":
        if elapsed > 3:
            cycle_state_pedestrian(GREEN)
            ss2_state, ss2_state_start = "PED_GREEN", now
 
    elif ss2_state == "PED_GREEN":
        if elapsed > 3:
            set_shift2(TL4_MASK | TL5_MASK |PED_MASK , RED_TL4 | RED_TL5)  # traffic lights solid red
            ss2_flash_state = False
            ss2_flash_last_toggle = now
            ss2_state, ss2_state_start = "PED_FLASH", now

    elif ss2_state == "PED_FLASH":
        if elapsed >= 2:
            cycle_state_pedestrian(RED)
            if ss2_hold_requested:
                cycle_state_pedestrian(GREEN)
                ss2_state, ss2_state_start = "TL_HOLD", now
            else:
                ss2_state, ss2_state_start = "TL4_GREEN", now
        elif now - ss2_flash_last_toggle >= 0.125:
            ss2_flash_state = not ss2_flash_state
            set_shift2(PED_MASK, RED_PED if ss2_flash_state else 0)
            ss2_flash_last_toggle = now

    elif ss2_state == "TL_HOLD":
        if not ss2_hold_requested:
            ss2_flash_state = False
            ss2_flash_last_toggle = now
            ss2_state, ss2_state_start = "PED_FLASH", now

def ss3_step(now):
    global ss3_phase, ss3_phase_start, ss3_hold_active, ss3_hold_start, ss2_hold_requested
    is_overheight,is_day = overheight["us5"],ldr_reading["ldr_DS1"]
    green_time = 5 if is_day else 10

    if ss3_phase == "normal":
        if is_overheight:
            if not ss3_hold_active:
                ss3_hold_active = True
                ss3_hold_start = now
                ss2_hold_requested = True

            if (now - ss3_hold_start >= 3) and ss2_state == "TL_HOLD":
                overheight_state_ss3()
                ss3_phase, ss3_phase_start = "green", now
                ss3_hold_active = False
        elif ss3_hold_active:
            # overheight cleared before the hold finished — cancel it
            ss3_hold_active = False
            ss2_hold_requested = False

    elif ss3_phase == "green":
        if now - ss3_phase_start >= green_time: #time green
            if is_overheight:
               pass
            else:
                yellow_state_ss3()
                ss3_phase, ss3_phase_start = "yellow", now

    elif ss3_phase == "yellow": # time yellow
        if now - ss3_phase_start >= 3:
            normal_state_ss3()
            ss3_phase = "normal"
            ss2_hold_requested = False

def ss4_step(is_overheight, us5_just_exited):
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
    global us5_was_overheight
    while True:
        try: 
            #Validation loop
            overHeightLimit = None
            while overHeightLimit is None or overHeightLimit < 0 or overHeightLimit > TOP_HEIGHT:
                limitInput = input("Enter the height limit (m): ").strip()
                try:
                    if limitInput == "":
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



            lastPollTime = time.time()
            while True:
                currentTime = time.time()
                if (currentTime - lastPollTime) >= pollingRate:
                    lastPollTime = currentTime


                    # reads & calcuations
                    heightUS1 = heightDiff(board.sonar_read(triggerPinUS1))
                    heightUS2 = heightDiff(board.sonar_read(triggerPinUS2))
                    heightUS3 = heightDiff(board.sonar_read(triggerPinUS3))
                    heightUS4 = heightDiff(board.sonar_read(triggerPinUS4))
                    heightUS5 = heightDiff(board.sonar_read(triggerPinUS5))
                    valueDS1 = board.analog_read(ldrPinDS1)[0]
                    valueDS2 = board.analog_read(ldrPinDS2)[0]
                    
                    lowerErrorBound = heightUS3*(1- acceptableError/100)
                    upperErrorBound = heightUS3*(1+ acceptableError/100)


                    overheight["us1"] = heightUS1 >= overHeightLimit
                    overheight["us2"] = heightUS2 >= overHeightLimit
                    overheight["us3"] = heightUS3 >= overHeightLimit
                    overheight["us4"] = heightUS4 >= overHeightLimit
                    overheight["us5"] = heightUS5 >= overHeightLimit

                    ldr_reading["ldr_DS1"] = valueDS1 >= calibrated_value_day
                    ldr_reading["ldr_DS2"] = valueDS2 >= calibrated_value_day

                    us5_just_exited = us5_was_overheight and not overheight["us5"]
                    us5_was_overheight = overheight["us5"]
                    
                    print(f"US3 height: {heightUS3:.2f} cm \n US4 height: {heightUS4:.2f} cm \n US5 height: {heightUS5:.2f} cm \n DS1 reading:{valueDS1:.2f}")
                    # execution & logic
                    is_over_ss4 = overheight["us3"] and lowerErrorBound <= heightUS4 <= upperErrorBound

                    
                    
                    ss1_step(currentTime)
                    ss2_step(currentTime)
                    ss3_step(currentTime)
                    ss4_step(is_over_ss4, us5_just_exited)
                    
        except KeyboardInterrupt:
            update_3_chips(0x00, 0x00, 0x00)
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()