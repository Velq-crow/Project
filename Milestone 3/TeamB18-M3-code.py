# Created Date:6/9/26
# Created By: Ketan
# Version: 3.0


from pymata4 import pymata4
import time

board = pymata4.Pymata4()

# Constants
TOP_HEIGHT = 10 #cm  # Distance from the sensors to the road surface
pollingRate  = 1  # seconds between each full sensor poll
calibrated_value_day = 800  # LDR analog reading at or above this is treated as day

# Shift register control pins (A0 = 14, A1 = 15, A2 = 16 when used as digital pins)
DATA_PIN  = 14 
CLOCK_PIN = 16
LATCH_PIN = 15 


# SS3 and SS4 LED bit masks (shift register chip 3)
RED_TL6    = 0x20 # Pin 6
GREEN_TL6  = 0x08 # Pin 4
YELLOW_TL6 = 0x10 # Pin 5
GREEN_TL3  = 0x40 # Pin 7
RED_TL3    = 0x80 # Pin 8

# SS2 LED bit masks (shift register chip 1). "Pin N" is the connector pin number.
RED_TL5    = 0x40  # Pin 7
RED_TL4    = 0x80  # Pin 8
YELLOW_TL5 = 0x08  # Pin 4
YELLOW_TL4 = 0x01  # Pin 1
GREEN_TL5  = 0x04  # Pin 3
GREEN_TL4  = 0x20  # Pin 6
RED_PED    = 0x02  # Pin 2
GREEN_PED  = 0x10  # Pin 5
redPedFlashing = 8  # Arduino pin that is ORed with RED_PED to flash the red pedestrian light

# SS1 LED, warning light and buzzer bit masks (shift register chip 2)
GREEN_TL2  = 0x40  # Pin 7
GREEN_TL1  = 0x20  # Pin 6
YELLOW_TL2 = 0x80  # Pin 8
YELLOW_TL1 = 0x10  # Pin 5
RED_TL2    = 0x08  # Pin 4
RED_TL1    = 0x04  # Pin 3
LIGHTS_WL1 = 0x02  # Pin 2
BUZZER_PA1 = 0x01  # Pin 1

# Masks covering every bit that belongs to one light, used so set_shift only
# changes that light and leaves the other bits on the chip alone
TL6_MASK = RED_TL6 | YELLOW_TL6 | GREEN_TL6
TL5_MASK = RED_TL5 | YELLOW_TL5 | GREEN_TL5
TL4_MASK = RED_TL4 | YELLOW_TL4 | GREEN_TL4
TL3_MASK = RED_TL3 | GREEN_TL3
TL2_MASK = GREEN_TL2 | YELLOW_TL2 | RED_TL2
TL1_MASK = GREEN_TL1 | YELLOW_TL1 | RED_TL1
PED_MASK = RED_PED | GREEN_PED
PA1_MASK = BUZZER_PA1
WL1_MASK = LIGHTS_WL1

# Current output byte held for each shift register chip
chip3_state = 0x00  # SS3 and SS4
chip2_state = 0x00  # SS1
chip1_state = 0x00  # SS2


# Overheight flag for each ultrasonic sensor (True = vehicle is over the limit)
overheight = {
    "us1": False, "us2": False,
    "us3": False, "us4": False,
    "us5": False,
}

# Day/night flag for each LDR (True = day)
ldr_reading = {
    "ldr_DS1": True,
    "ldr_DS2": True
}

# US5 (TL6 / ss3)
echoPinUS5    = 5
triggerPinUS5 = 13
us5_was_overheight = False  # US5 overheight result from the previous poll
us5_just_exited = False     # True for one poll after an overheight vehicle leaves US5
ss3_phase = "normal"   # normal, green, yellow
ss3_phase_start = 0.0  # time the current SS3 phase began

# US3 / US4 (TL3 / ss4)
triggerPinUS3 = 11
echoPinUS3    = 6
triggerPinUS4 = 12
echoPinUS4    = 7
acceptableError = 10  # percent difference allowed between US3 and US4 heights
ss4_phase = "normal"  # normal, overheight

# SS2
ss2_state = "TL4_GREEN"        # current state of the SS2 state machine
ss2_state_start = time.time()  # time the current SS2 state began
ss2_ped_requested = False      # True once the pedestrian button has been pressed
ss3_hold_active = False        # True while SS3 is waiting for SS2 to reach TL_HOLD
ss3_hold_start = 0.0           # time SS3 started requesting the hold
ss2_hold_requested = False     # SS3 asks SS2 to hold TL4/TL5 on red
ss1_override_last_seen = 0.0   # last time the SS1 override condition was seen (not used yet)

# US1 & TL1
echoPinUS1    = 4
triggerPinUS1 = 9
ss1_TL1_phase = "green"   # red, green, yellow
ss1_TL1_phase_start = 0.0 # time the current TL1 phase began

# US2 & TL2
echoPinUS2    = 3
triggerPinUS2 = 10
ss1_TL2_phase = "green"   # red, green, yellow
ss1_TL2_phase_start = 0.0 # time the current TL2 phase began
ss1_was_overridden = False  # True while SS1 is in the override (reds, buzzer, WL1)

# LDR analog pins (A4 and A3) and the pedestrian push button pin
ldrPinDS1 = 4
ldrPinDS2 = 3
pedestrianButton=2

last_refresh = 0.0  # time of the last forced light refresh (not used yet)

# Values passed to cycle_state_pedestrian
GREEN = True
RED = False

last_sent = None  # last 24-bit value sent to the shift registers (used by the redundant-send check)


# Configure the shift register control pins as outputs
board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)

# Flashing pin starts low so the red pedestrian light is not flashing at start up
board.set_pin_mode_digital_output(redPedFlashing)
board.digital_write(redPedFlashing, 0)

# Pedestrian button is wired with the internal pull-up resistor
board.set_pin_mode_digital_input_pullup(pedestrianButton)


# Register each ultrasonic sensor (trigger, echo). Timeout is in microseconds.
board.set_pin_mode_sonar(triggerPinUS5, echoPinUS5, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS3, echoPinUS3, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS4, echoPinUS4, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS1, echoPinUS1, timeout=200000)
board.set_pin_mode_sonar(triggerPinUS2, echoPinUS2, timeout=200000)
board.set_pin_mode_analog_input(ldrPinDS1)
board.set_pin_mode_analog_input(ldrPinDS2)


# Allow Firmata time to finish configuring the pins before they are used
time.sleep(1)

def any_overheight():
    """
    Used to check whether any of the five ultrasonic sensors currently sees an overheight vehicle.

        Parameters:
            function has no parameters

        Returns:
            True if at least one entry in the overheight dictionary is True, otherwise False
    """
    return any(overheight.values())

def shift_out(value, num_bits=8, msb_first=True):
    """
    Used to bit-bang a value out to the daisy-chained 74HC595 shift registers
    (data on DATA_PIN, clock on CLOCK_PIN) and latch it onto the outputs with LATCH_PIN.

        Parameters:
            value (int): The bits to send, with the first chip's byte in the lowest 8 bits
            num_bits (int): How many bits to send (24 for three chips)
            msb_first (bool): True to send the most significant bit first

        Returns:
            function has no return
    """
    # Hold the latch low so the outputs do not change while shifting
    board.digital_write(LATCH_PIN, 0)
    bit_range = range(num_bits - 1, -1, -1) if msb_first else range(num_bits)
    for i in bit_range:
        # Put the next bit on the data line, then pulse the clock to shift it in.
        # The short sleeps keep the serial link from being flooded and corrupting data.
        bit = (value >> i) & 1
        board.digital_write(DATA_PIN, bit)
        time.sleep(0.001)
        board.digital_write(CLOCK_PIN, 1)
        time.sleep(0.001)
        board.digital_write(CLOCK_PIN, 0)
        time.sleep(0.001)
    # Raising the latch copies the shifted bits onto the LED outputs
    board.digital_write(LATCH_PIN, 1)
    time.sleep(0.005)


def update_3_chips(chip3_val, chip2_val, chip1_val):
    """
    Used to combine the three chip bytes into one 24-bit value and shift it out.
    The redundant-send check (skip if unchanged) is included to ensure minmimal sending of shift register commands.

        Parameters:
            chip3_val (int): Byte for chip 3 (SS3 and SS4), sent first so it ends up furthest along the chain
            chip2_val (int): Byte for chip 2 (SS1)
            chip1_val (int): Byte for chip 1 (SS2), sent last so it ends up on the first chip

        Returns:
            function has no return
    """
    global last_sent
    combined = (chip3_val << 16) | (chip2_val << 8) | chip1_val
    if combined == last_sent:
        return
    last_sent = combined
    shift_out(combined, num_bits=24)

def set_shift3(mask, bits_on):
    """
    Used to change only the masked bits of chip 3 (SS3 and SS4) and update all the chips.

        Parameters:
            mask (int): Bits of chip 3 that this call is allowed to change
            bits_on (int): Bits that should be on; masked bits missing from here are turned off

        Returns:
            function has no return
    """
    global chip3_state
    # Clear the masked bits, then set the requested ones. Other bits are untouched.
    chip3_state = (chip3_state & ~mask) | (bits_on & mask)
    update_3_chips(chip3_state, chip2_state, chip1_state )

def set_shift2(mask, bits_on):
    """
    Used to change only the masked bits of chip 1 (SS2) and update all the chips.

        Parameters:
            mask (int): Bits of chip 1 that this call is allowed to change
            bits_on (int): Bits that should be on; masked bits missing from here are turned off

        Returns:
            function has no return
    """
    global chip1_state
    # Clear the masked bits, then set the requested ones. Other bits are untouched.
    chip1_state = (chip1_state & ~mask) | (bits_on & mask)
    update_3_chips(chip3_state, chip2_state, chip1_state )

def set_shift1(mask, bits_on):
    """
    Used to change only the masked bits of chip 2 (SS1) and update all the chips.

        Parameters:
            mask (int): Bits of chip 2 that this call is allowed to change
            bits_on (int): Bits that should be on; masked bits missing from here are turned off

        Returns:
            function has no return
    """
    global chip2_state
    # Clear the masked bits, then set the requested ones. Other bits are untouched.
    chip2_state = (chip2_state & ~mask) | (bits_on & mask)
    update_3_chips(chip3_state, chip2_state, chip1_state)

def heightDiff(distance):
    """
    Used to minus the distance measured by an ultrasonic sensor from the TOP_HEIGHT to give actual height of the vechicle.

        Parameters:
            distance (list): Result of board.sonar_read, [distance_cm, timestamp]

        Returns:
            Returns TOP_HEIGHT - distance[0], the vehicle height in cm
    """
    return TOP_HEIGHT - distance[0]

def overheight_state_ss4():
    """
    Used to turn TL3 red (overheight vehicle detected).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift3(TL3_MASK, RED_TL3)

def normal_state_ss4():
    """
    Used to turn TL3 green (normal traffic).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift3(TL3_MASK, GREEN_TL3)

def normal_state_ss3():
    """
    Used to turn TL6 red (normal state, nothing is allowed through).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift3(TL6_MASK, RED_TL6)

def overheight_state_ss3():
    """
    Used to turn TL6 green so the overheight vehicle can pass.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift3(TL6_MASK, GREEN_TL6)

def yellow_state_ss3():
    """
    Used to turn TL6 yellow (warning before it returns to red).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift3(TL6_MASK, YELLOW_TL6)

def tl4_cycle_state():
    """
    Used to turn TL4 green and TL5 red.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift2(TL4_MASK | TL5_MASK, GREEN_TL4 | RED_TL5)

def tl4_cycle_state_off():
    """
    Used to turn TL4 yellow at the end of its green time.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift2(TL4_MASK, YELLOW_TL4)

def tl5_cycle_state():
    """
    Used to turn TL5 green and TL4 red.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift2(TL4_MASK | TL5_MASK, GREEN_TL5 | RED_TL4)

def tl5_cycle_state_off():
    """
    Used to turn TL5 yellow at the end of its green time.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift2(TL5_MASK, YELLOW_TL5)

def cycle_state_pedestrian(state):
    """
    Used to set the pedestrian lights. GREEN gives the pedestrians a green
    and holds TL4 and TL5 on red. RED returns the pedestrian light to red.

        Parameters:
            state (bool): GREEN to let pedestrians cross, RED to stop them

        Returns:
            function has no return
    """
    if state == GREEN:
        set_shift2(PED_MASK | TL4_MASK | TL5_MASK, GREEN_PED | RED_TL4 | RED_TL5)
    else:
        set_shift2(PED_MASK, RED_PED)

def normal_state_ss1_TL1():
    """
    Used to turn TL1 green (normal state).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL1_MASK,GREEN_TL1)

def normal_state_ss1_TL2():
    """
    Used to turn TL2 green (normal state).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL2_MASK,GREEN_TL2)

def yellow_state_ss1_TL1():
    """
    Used to turn TL1 yellow (warning before red).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL1_MASK,YELLOW_TL1)

def yellow_state_ss1_TL2():
    """
    Used to turn TL2 yellow (warning before red).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL2_MASK,YELLOW_TL2)

def overheight_state_ss1_TL1():
    """
    Used to turn TL1 red (overheight vehicle detected by US1).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL1_MASK,RED_TL1)

def overheight_state_ss1_TL2():
    """
    Used to turn TL2 red (overheight vehicle detected by US2).

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL2_MASK,RED_TL2)

def enter_override():
    """
    Used to start the SS1 override: TL1 and TL2 red, buzzer (PA1) and warning lights (WL1) on.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    set_shift1(TL1_MASK | TL2_MASK | PA1_MASK | WL1_MASK, RED_TL1 | RED_TL2 | BUZZER_PA1 | LIGHTS_WL1)

def exit_override():
    """
    Used to end the SS1 override: TL1 and TL2 back to green, buzzer and warning lights off.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    # PA1/WL1 bits are in mask but not in bits_on -> cleared
    set_shift1(TL1_MASK | TL2_MASK | PA1_MASK | WL1_MASK, GREEN_TL1 | GREEN_TL2)

def ss1_step(now):
    """
    Used to run one step of Subsystem 1. TL1 and TL2 go yellow for 1 s then red for
    30 s when US1 or US2 sees an overheight vehicle. If both US3 and US4 see an
    overheight vehicle the override takes over (reds, buzzer and warning lights).

        Parameters:
            now (float): Current time in seconds from time.time()

        Returns:
            function has no return
    """
    global ss1_TL1_phase, ss1_TL1_phase_start, ss1_TL2_phase, ss1_TL2_phase_start
    global ss1_was_overridden

    # Override is active when both US3 and US4 see an overheight vehicle
    override = overheight["us3"] and overheight["us4"]
    is_overheight_US1 = overheight["us1"]
    is_overheight_US2 = overheight["us2"]

    # Required output of the exact time and overheight
    if is_overheight_US1:
        print(f"{board.sonar_read(triggerPinUS1)[1]} time of overhight detected by US1")

    if override:
        # Only switch the lights on the first poll of the override
        if not ss1_was_overridden:
            enter_override()
            ss1_TL1_phase, ss1_TL1_phase_start = "red", now
            ss1_TL2_phase, ss1_TL2_phase_start = "red", now
            ss1_was_overridden = True
        return

    # Override just ended, so return both lights to green
    if ss1_was_overridden:
        exit_override()
        ss1_TL1_phase, ss1_TL1_phase_start = "green", now
        ss1_TL2_phase, ss1_TL2_phase_start = "green", now
        ss1_was_overridden = False

    # --- 1.R2: TL1 driven by US1 ---
    if ss1_TL1_phase == "green":
        # Overheight vehicle at US1 starts the yellow warning
        if is_overheight_US1:
            yellow_state_ss1_TL1()
            ss1_TL1_phase, ss1_TL1_phase_start = "yellow", now

    elif ss1_TL1_phase == "yellow":
        # Yellow lasts 1 s, then red
        if now - ss1_TL1_phase_start >= 1:
            overheight_state_ss1_TL1()
            ss1_TL1_phase, ss1_TL1_phase_start = "red", now

    elif ss1_TL1_phase == "red":
        # Red lasts 30 s, then back to green
        if now - ss1_TL1_phase_start >= 30:
            normal_state_ss1_TL1()
            ss1_TL1_phase = "green"

    # --- TL2 driven by US2 ---
    if ss1_TL2_phase == "green":
        if is_overheight_US2 and ss1_TL1_phase == "green":
            # TL1 is still green, so both lights go yellow together

            yellow_state_ss1_TL1()
            ss1_TL1_phase, ss1_TL1_phase_start = "yellow", now

            yellow_state_ss1_TL2()
            ss1_TL2_phase, ss1_TL2_phase_start = "yellow", now

        elif is_overheight_US2 and ss1_TL1_phase != "green":
            # TL1 is already yellow or red, so only TL2 changes
            yellow_state_ss1_TL2()
            ss1_TL2_phase, ss1_TL2_phase_start = "yellow", now

    elif ss1_TL2_phase == "yellow":
        # Yellow lasts 1 s, then red
        if now - ss1_TL2_phase_start >= 1:
            overheight_state_ss1_TL2()
            ss1_TL2_phase, ss1_TL2_phase_start = "red", now

    elif ss1_TL2_phase == "red":
        # Red lasts 30 s, then back to green
        if now - ss1_TL2_phase_start >= 30:
            normal_state_ss1_TL2()
            ss1_TL2_phase = "green"

def ss2_step(now):
    """
    Used to run one step of Subsystem 2: the TL4/TL5 cycle, the pedestrian crossing
    (button, green ped, flashing red ped) and the hold requested by SS3.
    States: TL4_GREEN, TL4_YELLOW, TL5_GREEN, TL5_YELLOW, PED_YELLOW, PED_GREEN,
    PED_FLASH, TL_HOLD.

        Parameters:
            now (float): Current time in seconds from time.time()

        Returns:
            function has no return
    """
    global ss2_state, ss2_state_start, ss2_ped_requested

    # Green times (seconds) depend on whether it is day or night
    is_day = ldr_reading["ldr_DS2"]
    elapsed = now - ss2_state_start
    if is_day:
        tl4_green_time = 20
        tl5_green_time = 10
    else:
        tl4_green_time = 30
        tl5_green_time = 5

    # The button is only checked while the normal TL4/TL5 cycle is running
    if ss2_state in ("TL4_GREEN", "TL5_GREEN", "TL4_YELLOW", "TL5_YELLOW"):
        if board.digital_read(pedestrianButton)[0] == 1:
            print("button pressed")
            ss2_ped_requested = True

    if ss2_state == "TL4_GREEN":
        tl4_cycle_state()
        if ss2_ped_requested:
            # Pedestrian button pressed: TL4 yellow, then the pedestrian sequence
            tl4_cycle_state_off()
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif ss2_hold_requested:
            # SS3 wants traffic stopped
            tl4_cycle_state_off()
            ss2_state, ss2_state_start = "TL4_YELLOW", now
        elif elapsed > tl4_green_time:
            # Green time finished
            tl4_cycle_state_off()
            ss2_state, ss2_state_start = "TL4_YELLOW", now

    elif ss2_state == "TL4_YELLOW":
        if ss2_ped_requested:
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif elapsed > 3:
            # Yellow finished: go to the hold if SS3 asked, otherwise swap to TL5
            if ss2_hold_requested:
                cycle_state_pedestrian(GREEN)
                ss2_state, ss2_state_start = "TL_HOLD", now
            else:
                ss2_state, ss2_state_start = "TL5_GREEN", now

    elif ss2_state == "TL5_GREEN":
        tl5_cycle_state()
        if ss2_ped_requested:
            # Pedestrian button pressed: TL5 yellow, then the pedestrian sequence
            tl5_cycle_state_off()
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif ss2_hold_requested:
            # SS3 wants traffic stopped
            tl5_cycle_state_off()
            ss2_state, ss2_state_start = "TL5_YELLOW", now
        elif elapsed > tl5_green_time:
            # Green time finished
            tl5_cycle_state_off()
            ss2_state, ss2_state_start = "TL5_YELLOW", now

    elif ss2_state == "TL5_YELLOW":
        if ss2_ped_requested:
            ss2_ped_requested = False
            ss2_state, ss2_state_start = "PED_YELLOW", now
        elif elapsed > 3:
            # Yellow finished: go to the hold if SS3 asked, otherwise swap to TL4
            if ss2_hold_requested:
                cycle_state_pedestrian(GREEN)
                ss2_state, ss2_state_start = "TL_HOLD", now
            else:
                ss2_state, ss2_state_start = "TL4_GREEN", now

    elif ss2_state == "PED_YELLOW":
        # After 3 s of yellow the pedestrians get a green and TL4/TL5 go red
        if elapsed > 3:
            cycle_state_pedestrian(GREEN)
            ss2_state, ss2_state_start = "PED_GREEN", now

    elif ss2_state == "PED_GREEN":
        # After 3 s of green ped, turn the ped light off (the flashing red starts next)
        if elapsed > 3:
            set_shift2(TL4_MASK | TL5_MASK |PED_MASK , RED_TL4 | RED_TL5)  # traffic lights solid red
            ss2_state, ss2_state_start = "PED_FLASH", now

    elif ss2_state == "PED_FLASH":
        if elapsed >= 2:
            # Flash finished: ped back to solid red and the flashing pin off
            cycle_state_pedestrian(RED)
            board.digital_write(redPedFlashing,0)
            if ss2_hold_requested:
                cycle_state_pedestrian(GREEN)
                ss2_state, ss2_state_start = "TL_HOLD", now
            else:
                ss2_state, ss2_state_start = "TL4_GREEN", now
        else:
            # Flash in progress: RED_PED bit off and the flashing pin on
            set_shift2(PED_MASK, 0)
            board.digital_write(redPedFlashing,1)

    elif ss2_state == "TL_HOLD":
        # TL4/TL5 stay red until SS3 releases the hold, then flash the ped light and resume
        if not ss2_hold_requested:
            set_shift2(PED_MASK,0)
            ss2_state, ss2_state_start = "PED_FLASH", now

def ss3_step(now):
    """
    Used to run one step of Subsystem 3 (TL6). When US5 sees an overheight vehicle it asks
    SS2 to hold TL4/TL5, then turns TL6 green. After the green time it goes yellow, then back to red.

        Parameters:
            now (float): Current time in seconds from time.time()

        Returns:
            function has no return
    """
    global ss3_phase, ss3_phase_start, ss3_hold_active, ss3_hold_start, ss2_hold_requested
    is_overheight,is_day = overheight["us5"],ldr_reading["ldr_DS1"]
    # TL6 green time (seconds) is shorter in the day than at night
    green_time = 5 if is_day else 10

    if ss3_phase == "normal":
        if is_overheight:
            # Ask SS2 to hold its lights the first time the vehicle is seen
            if not ss3_hold_active:
                ss3_hold_active = True
                ss3_hold_start = now
                ss2_hold_requested = True

            # Wait 3 s and for SS2 to reach TL_HOLD before turning TL6 green
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
               # Another overheight vehicle is still at US5, so keep TL6 green
               pass
            else:
                yellow_state_ss3()
                ss3_phase, ss3_phase_start = "yellow", now

    elif ss3_phase == "yellow": # time yellow
        # After 3 s of yellow, TL6 returns to red and SS2 is released
        if now - ss3_phase_start >= 3:
            normal_state_ss3()
            ss3_phase = "normal"
            ss2_hold_requested = False

def ss4_step(is_overheight, us5_just_exited):
    """
    Used to run one step of Subsystem 4 (TL3). TL3 goes red when an overheight vehicle is
    confirmed by US3 and US4, and returns to green once it has left through US5 and no
    other overheight vehicle is detected.

        Parameters:
            is_overheight (bool): True if US3 is overheight and US4 agrees within acceptableError
            us5_just_exited (bool): True on the poll where an overheight vehicle leaves US5

        Returns:
            function has no return
    """
    global ss4_phase

    if ss4_phase == "normal":
        # Overheight vehicle confirmed: stop traffic with a red TL3
        if is_overheight:
            overheight_state_ss4()
            ss4_phase = "overheight"
    elif ss4_phase == "overheight":
        # Release TL3 only once the vehicle has exited and nothing else is overheight
        if us5_just_exited and not any_overheight():
            normal_state_ss4()
            ss4_phase = "normal"

def init_lights():
    """
    Used to put every light in its starting state before the main loop begins.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    normal_state_ss1_TL1()
    normal_state_ss1_TL2()
    normal_state_ss3()
    normal_state_ss4()
    tl4_cycle_state()                # TL4 green, TL5 red
    set_shift2(PED_MASK, RED_PED)


def main():
    """
    Used to run the whole system: ask for the height limit, then repeatedly poll the
    sensors and run the four subsystem steps. Ctrl+C turns all lights off and exits.

        Parameters:
            function has no parameters

        Returns:
            function has no return
    """
    global us5_was_overheight
    while True:
        try:
            #Validation loop
            # Keep asking until the limit is a whole number between 0 and TOP_HEIGHT
            overHeightLimit = None
            while overHeightLimit is None or overHeightLimit < 0 or overHeightLimit > TOP_HEIGHT:
                limitInput = input("Enter the height limit (m): ").strip()
                try:
                    # Pressing Enter with no input uses the default limit
                    if limitInput == "":
                        print("Assigning default height")
                        overHeightLimit = 4
                        break

                    overHeightLimit = int(limitInput)

                    if overHeightLimit < 0:
                        print("Invalid input. height limit cannot be negative.")
                        overHeightLimit = None

                    elif overHeightLimit > TOP_HEIGHT:
                        print(f"Invalid input. height limit cannot be more than {TOP_HEIGHT}.")
                        overHeightLimit = None
                except ValueError:
                    print("Invalid input. Please enter a whole number.")


            init_lights()
            lastPollTime = time.time()
            while True:
                currentTime = time.time()
                # Only poll the sensors once every pollingRate seconds
                if (currentTime - lastPollTime) >= pollingRate:
                    lastPollTime = currentTime


                    # reads & calcuations
                    # The 0.1 s sleeps stop neighbouring sensors picking up each other's echoes
                    heightUS1 = heightDiff(board.sonar_read(triggerPinUS1))
                    time.sleep(0.1)
                    heightUS2 = heightDiff(board.sonar_read(triggerPinUS2))
                    time.sleep(0.1)

                    heightUS3 = heightDiff(board.sonar_read(triggerPinUS3))
                    heightUS4 = heightDiff(board.sonar_read(triggerPinUS4))
                    time.sleep(0.1)

                    heightUS5 = heightDiff(board.sonar_read(triggerPinUS5))
                    time.sleep(0.1)

                    valueDS1 = board.analog_read(ldrPinDS1)[0]
                    valueDS2 = board.analog_read(ldrPinDS2)[0]

                    # US4 must be within acceptableError percent of US3 to count as the same vehicle
                    lowerErrorBound = heightUS3*(1- acceptableError/100)
                    upperErrorBound = heightUS3*(1+ acceptableError/100)


                    # Compare each measured height with the limit
                    overheight["us1"] = heightUS1 >= overHeightLimit
                    overheight["us2"] = heightUS2 >= overHeightLimit
                    overheight["us3"] = heightUS3 >= overHeightLimit
                    overheight["us4"] = heightUS4 >= overHeightLimit
                    overheight["us5"] = heightUS5 >= overHeightLimit

                    # Day if the LDR reading is at or above the calibrated value
                    ldr_reading["ldr_DS1"] = valueDS1 >= calibrated_value_day
                    ldr_reading["ldr_DS2"] = valueDS2 >= calibrated_value_day

                    # True only on the poll where US5 changes from overheight to not overheight
                    us5_just_exited = us5_was_overheight and not overheight["us5"]
                    us5_was_overheight = overheight["us5"]

                    # Debug output of all sensor readings
                    # print(f"US1 height: {heightUS1:.2f} cm \n US2 height: {heightUS2:.2f} cm \n US3 height: {heightUS3:.2f} cm \n US4 height: {heightUS4:.2f} cm \n US5 height: {heightUS5:.2f} cm \n DS1 reading:{valueDS1:.2f} \n DS2 reading:{valueDS2:.2f}")
                    # execution & logic
                    # TL3 is only triggered when US3 is overheight and US4 agrees with its reading
                    is_over_ss4 = overheight["us3"] and lowerErrorBound <= heightUS4 <= upperErrorBound



                    # Run each subsystem once with the latest readings
                    ss1_step(currentTime)
                    ss2_step(currentTime)
                    ss3_step(currentTime)
                    ss4_step(is_over_ss4, us5_just_exited)


        except KeyboardInterrupt:
            # Ctrl+C: turn every light off, stop the flashing pin and exit
            update_3_chips(0x00, 0x00, 0x00)
            board.digital_write(redPedFlashing,0)

            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()
