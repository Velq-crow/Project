# Subsystem 2 Eng1013
# Version: 1.1

from pymata4 import pymata4
import time
import random

board = pymata4.Pymata4()
#polling time
pollingTime = 0.2


#TL5
redPinTL5 =13
yellowPinTL5 =12
greenPinTL5 = 11

#TL4
redPinTL4 =10
yellowPinTL4 =9
greenPinTL4 = 8

#PL1 and PL2 do in series
redPinPL1 = 6
greenPinPL1 = 7

#PB1/2
pedestrianButton=2

#Configuring pins
board.set_pin_mode_digital_output(redPinTL5)
board.set_pin_mode_digital_output(yellowPinTL5)
board.set_pin_mode_digital_output(greenPinTL5)

board.set_pin_mode_digital_output(redPinTL4)
board.set_pin_mode_digital_output(yellowPinTL4)
board.set_pin_mode_digital_output(greenPinTL4)

board.set_pin_mode_digital_output(redPinPL1)
board.set_pin_mode_digital_output(greenPinPL1)

board.set_pin_mode_digital_input_pullup(pedestrianButton)


def tl4_cycle_state():
    board.digital_pin_write(greenPinTL4,1)
    board.digital_pin_write(yellowPinTL4,0)
    board.digital_pin_write(redPinTL4,0)

    board.digital_pin_write(greenPinTL5,0)
    board.digital_pin_write(yellowPinTL5,0)
    board.digital_pin_write(redPinTL5,1)

def tl4_cycle_state_off():
    board.digital_pin_write(greenPinTL4,0)
    board.digital_pin_write(yellowPinTL4,1)
    board.digital_pin_write(redPinTL4,0)

    board.digital_pin_write(greenPinTL5,0)
    board.digital_pin_write(yellowPinTL5,0)
    board.digital_pin_write(redPinTL5,1)

def tl5_cycle_state():
    board.digital_pin_write(greenPinTL4,0)
    board.digital_pin_write(yellowPinTL4,0)
    board.digital_pin_write(redPinTL4,1)

    board.digital_pin_write(greenPinTL5,1)
    board.digital_pin_write(yellowPinTL5,0)
    board.digital_pin_write(redPinTL5,0)

def tl5_cycle_state_off():
    board.digital_pin_write(greenPinTL4,0)
    board.digital_pin_write(yellowPinTL4,0)
    board.digital_pin_write(redPinTL4,1)

    board.digital_pin_write(greenPinTL5,0)
    board.digital_pin_write(yellowPinTL5,1)
    board.digital_pin_write(redPinTL5,0)

def cycle_state_pedestrian():
    board.digital_pin_write(greenPinTL4,0)
    board.digital_pin_write(yellowPinTL4,0)
    board.digital_pin_write(redPinTL4,1)

    board.digital_pin_write(greenPinTL5,0)
    board.digital_pin_write(yellowPinTL5,0)
    board.digital_pin_write(redPinTL5,1)

def pedestrian_lights_tl4():
    tl4_cycle_state_off()
    time.sleep(3)
    cycle_state_pedestrian()
    board.digital_write(greenPinPL1,1)
    time.sleep(3)
    board.digital_write(greenPinPL1,0)
    lastTimeRed = time.time()
    while True:
        board.digital_write(redPinPL1,1)
        time.sleep(0.2)
        board.digital_write(redPinPL1,0)
        currentTimered = time.time()
        if currentTimered-lastTimeRed>2:
            break
        board.digital_write(redPinPL1,1)

def pedestrian_lights_tl5():
    tl5_cycle_state_off()
    time.sleep(3)
    cycle_state_pedestrian()
    board.digital_write(greenPinPL1,1)
    time.sleep(3)
    board.digital_write(greenPinPL1,0)
    lastTimeRed = time.time()
    while True:
        board.digital_write(redPinPL1,1)
        time.sleep(0.2)
        board.digital_write(redPinPL1,0)
        currentTimered = time.time()
        if currentTimered-lastTimeRed>2:
            break
        board.digital_write(redPinPL1,1)
    

def main():
    time.sleep(1)
    while True:
        try: 
            board.digital_pin_write(redPinPL1,1)
            # 20 second green
            lastTime = time.time()
            while True:
                currentTime =  time.time()
                result = board.digital_read(pedestrianButton)[0]
                if result == 0:
                    print("button pressed")
                    pedestrian_lights_tl4()
                    board.digital_pin_write(redPinPL1,1)
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
                    pedestrian_lights_tl5()
                    board.digital_pin_write(redPinPL1,1)
                if currentTime - lastTime > 10:
                    break
                tl5_cycle_state()
                time.sleep(pollingTime)

            
            #yellow 3 seconds
            tl5_cycle_state_off()
            time.sleep(3)

        except KeyboardInterrupt:
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()