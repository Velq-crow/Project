from pymata4 import pymata4
import time

# DATA_PIN  = 13
# CLOCK_PIN = 11
# LATCH_PIN = 12

DATA_PIN  = 14 #a0 
CLOCK_PIN = 16 #a2
LATCH_PIN = 15 #a1

board = pymata4.Pymata4()
pedestrianButton=2

board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)
board.set_pin_mode_digital_input(pedestrianButton)
board.set_pin_mode_digital_output(13)



board.set_pin_mode_digital_output(8)
board.set_pin_mode_digital_output(7)
#SS3 AND 4
RED_TL6    = 0x08
GREEN_TL6  = 0x02
YELLOW_TL6 = 0x04
GREEN_TL3  = 0x10
RED_TL3    = 0x20

#SS 2
RED_TL5    = 0x40  # Pin 8
RED_TL4    = 0x80  # Pin 7
YELLOW_TL5 = 0x08  # Pin 6
YELLOW_TL4 = 0x01  # Pin 5
GREEN_TL5  = 0x04  # Pin 4
GREEN_TL4  = 0x20  # Pin 3
RED_PED    = 0x02  # Pin 2
GREEN_PED  = 0x10  # Pin 1
redPedFlashing = 8

#SS 1
GREEN_TL2  = 0x40  # Pin 3
GREEN_TL1  = 0x20  # Pin 2
YELLOW_TL2 = 0x80  # Pin 5
YELLOW_TL1 = 0x10  # Pin 4
RED_TL2    = 0x08  # Pin 7
RED_TL1    = 0x04  # Pin 6
LIGHTS_WL1 = 0x02  # Pin 8
BUZZER_PA1 = 0x01  # Pin 1

TL6_MASK = RED_TL6 | YELLOW_TL6 | GREEN_TL6
TL5_MASK = RED_TL5 | YELLOW_TL5 | GREEN_TL5
TL4_MASK = RED_TL4 | YELLOW_TL4 | GREEN_TL4
TL3_MASK = RED_TL3 | GREEN_TL3
TL2_MASK = GREEN_TL2 | YELLOW_TL2 | RED_TL2
TL1_MASK = GREEN_TL1 | YELLOW_TL1 | RED_TL1
PED_MASK = RED_PED | GREEN_PED
PA1_MASK = BUZZER_PA1
WL1_MASK = LIGHTS_WL1

# US3 / US4 (TL3 / ss4)
triggerPinUS3 = 5
echoPinUS3    = 4
triggerPinUS4 = 7
echoPinUS4    = 6
acceptableError = 10  # percent
ss4_phase = "normal"
# SS2
ss2_state = "TL4_GREEN"
ss2_state_start = time.time()
ss2_ped_requested = False
ss3_hold_active = False
ss3_hold_start = 0.0
ss2_hold_requested = False
ss1_override_last_seen = 0.0   

# US1 & TL1
echoPinUS1    = 6
triggerPinUS1 = 5
ss1_TL1_phase = "green"   # red, green, yellow
ss1_TL1_phase_start = 0.0

# US2
echoPinUS2    = 4
triggerPinUS2 = 3
ss1_TL2_phase = "green"   # red, green, yellow
ss1_TL2_phase_start = 0.0
ss1_was_overridden = False

ldrPinDS1 = 4
ldrPinDS2 = 3
pedestrianButton=2

last_refresh = 0.0
time.sleep(1)

def shift_out(value, num_bits=8, msb_first=True):
    board.digital_write(LATCH_PIN, 0)
    bit_range = range(num_bits - 1, -1, -1) if msb_first else range(num_bits)
    for i in bit_range:
        bit = (value >> i) & 1
        board.digital_write(DATA_PIN, bit)
        board.digital_write(CLOCK_PIN, 1)
        board.digital_write(CLOCK_PIN, 0)
        time.sleep(0.01)
    board.digital_write(LATCH_PIN, 1)

def update_3_chips(chip3_val, chip2_val, chip1_val):
    combined = (chip3_val << 16) | (chip2_val << 8) | chip1_val
    shift_out(combined, num_bits=24)

def test_all_leds():
    # Flash each of the 24 LEDs one at a time
    update_3_chips(0x00, 0x00, 0x00)
    for n in range(24):
        value = 1 << n
        chip1_val = value & 0xFF
        chip2_val = (value >> 8) & 0xFF
        chip3_val = (value >> 16) & 0xFF
 
        if chip1_val:
            chip_num, led_hex = 1, chip1_val
        elif chip2_val:
            chip_num, led_hex = 2, chip2_val
        else:
            chip_num, led_hex = 3, chip3_val
 
        print(f"Chip {chip_num}: 0x{led_hex:02X}")
        
        update_3_chips(chip3_val, chip2_val, chip1_val)
        input("Press Enter for next LED...")
        
        update_3_chips(0x00, 0x00, 0x00)  # off before next LED
        time.sleep(0.5)
 
    # All LEDs on
    update_3_chips(0xFF, 0xFF, 0xFF)
    input("All on. Press Enter to turn off...")

 
    # All LEDs off
    update_3_chips(0x00, 0x00, 0x00)
def shift_no_latch(value, num_bits=24):
    board.digital_write(LATCH_PIN, 0)
    for i in range(num_bits - 1, -1, -1):
        board.digital_write(DATA_PIN, (value >> i) & 1)
        time.sleep(0.005)
        board.digital_write(CLOCK_PIN, 1)
        time.sleep(0.005)
        board.digital_write(CLOCK_PIN, 0)
        time.sleep(0.005)
    # no latch pulse, on purpose

def init_lights():
    """
    Used to put every light in its starting state with a single shift out.
 
        Parameters:
            function has no parameters
 
        Returns:
            function has no return
    """
    global chip1_state, chip2_state, chip3_state
 
    chip2_state = GREEN_TL1 | GREEN_TL2           # SS1: TL1 and TL2 green
    chip3_state = RED_TL6 | GREEN_TL3             # SS3: TL6 red, SS4: TL3 green
    chip1_state = GREEN_TL4 | RED_TL5 | RED_PED   # SS2: TL4 green, TL5 red, ped red
 
    update_3_chips(chip3_state, chip2_state, chip1_state)


def main():
    while True:
        try:
    
            print(board.digital_read(pedestrianButton))
            # init_lights()
            # time.sleep(1)
            # update_3_chips(0x00, 0x00, 0x00)    # known state: all off
            # shift_no_latch(0xFFFFFF)            # push 24 ones through, never latch
            # input("No LED should be lit. Did any flash? Press Enter...")
            # update_3_chips(0x00, 0x00, 0x00)
            # time.sleep(3)  
            # print("shift")
            # shift_out(0x01)
            # time.sleep(1)
            # test_all_leds()
            # update_3_chips(0xFF, 0xFF, 0x00)
            # time.sleep(1)
            # update_3_chips(0x00, 0x00, 0x00)
            # time.sleep(1)



            # time.sleep(1)
            # board.digital_pin_write(13,0)
            # time.sleep(1)
            # board.digital_pin_write(13,1)

            # print("chip 3")
            # time.sleep(2)
            # update_3_chips(0x00, 0xFF, 0x00)
            # print("chip 2")
            # time.sleep(2)
            # update_3_chips(0x00, 0x00, 0xFF)
            # print("chip 1")
            # time.sleep(2)

            # board.digital_pin_write()
            # time.sleep(2)
            # board.digital_write(7, 0)
            # time.sleep(3)


            # print("7")
            # update_3_chips(0x00, 0x00, 0x00)
            # board.digital_write(8,1 )            
            # time.sleep(3)  

            # print("shift")
            # update_3_chips(0xFF, 0xFF, 0xFF)
            # board.digital_write(8, 0)            
            # time.sleep(3)

            # print("none")
            # update_3_chips(0x00, 0x00, 0x00)
            # board.digital_write(8, 0)            
            # time.sleep(3)         

            
            
        except KeyboardInterrupt:
            update_3_chips(0x00, 0x00, 0x00)
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()



