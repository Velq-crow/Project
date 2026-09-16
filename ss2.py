# Subsystem 2 Eng1013
# Created Date:6/9/26
# Created By: Ketan
# Version: 1.2

from pymata4 import pymata4
import time
import random

board = pymata4.Pymata4()
#polling time
pollingTime = 0.2


DATA_PIN  = 12
CLOCK_PIN = 13
LATCH_PIN = 11
"""
Shift 1 
Pin 1: Red ped
Pin 2: Green traffic right side
Pin 3: Green traffic left side
Pin 4: Yello right
Pin 5: Yello left
Pin 6: red right
Pin 7: red left
Pin 8: green ped
tl4 is right side
tl5 is left side
"""

RED_PED    = 0x80  # Pin 1
GREEN_TL4  = 0x40  # Pin 2
GREEN_TL5  = 0x20  # Pin 3
YELLOW_TL4 = 0x10  # Pin 4
YELLOW_TL5 = 0x08  # Pin 5
RED_TL4    = 0x04  # Pin 6
RED_TL5    = 0x02  # Pin 7
GREEN_PED  = 0x01  # Pin 8

GREEN = True
RED = False
TL4 = True
TL5 = False
#PB1/2
pedestrianButton=2

#Configuring pins
board.set_pin_mode_digital_output(DATA_PIN)
board.set_pin_mode_digital_output(CLOCK_PIN)
board.set_pin_mode_digital_output(LATCH_PIN)

board.set_pin_mode_digital_input_pullup(pedestrianButton)

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

def set_shift2(value):
    update_3_chips(0x00, value, 0x00)

def tl4_cycle_state():
    set_shift2(RED_PED | GREEN_TL4 | RED_TL5)

def tl4_cycle_state_off():
    set_shift2(RED_PED | YELLOW_TL4 | RED_TL5)

def tl5_cycle_state():
    set_shift2(RED_PED | GREEN_TL5 | RED_TL4)

def tl5_cycle_state_off():
    set_shift2(RED_PED | YELLOW_TL5 | RED_TL4)

def cycle_state_pedestrian(BOOL):
    if BOOL == True:
        set_shift2(GREEN_PED | RED_TL4 | RED_TL5)
    elif BOOL == False:
        set_shift2(RED_PED | RED_TL4 | RED_TL5)

    
def pedestrian_lights(BOOL):
    if BOOL == True:
        tl4_cycle_state_off()
    if BOOL == False:
        tl5_cycle_state_off
    time.sleep(3)
    cycle_state_pedestrian(GREEN)
    time.sleep(3)
    cycle_state_pedestrian(RED)
    lastTimeRed = time.time()
    while True:
        #flashing tbd
        currentTimered = time.time()
        if currentTimered-lastTimeRed>2:
            break
        cycle_state_pedestrian(RED)


def main():
    time.sleep(1)
    while True:
        try: 
            # 20 second green
            lastTime = time.time()
            while True:
                currentTime =  time.time()
                result = board.digital_read(pedestrianButton)[0]
                if result == 0:
                    print("button pressed")
                    pedestrian_lights(TL4)
                if currentTime - lastTime > 20:
                    break
                tl4_cycle_state()
                time.sleep(pollingTime)
            
            #yellow 3 seconds
            tl4_cycle_state_off()
            time.sleep(3)

            # green 10 seconds
            lastTime = time.time()
            while True:
                currentTime =  time.time()
                result = board.digital_read(pedestrianButton)[0]
                if result == 0:
                    print("button pressed")
                    pedestrian_lights(TL5)
                if currentTime - lastTime > 10:
                    break
                tl5_cycle_state()
                time.sleep(pollingTime)

            
            #yellow 3 seconds
            tl5_cycle_state_off()
            time.sleep(3)

        except KeyboardInterrupt:
            update_3_chips(0x00, 0x00, 0x00)
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()