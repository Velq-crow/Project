# Subsystem 3 Eng1013
# Author: Ketan Karnati
# Last modified: 27/08/2026
# Version: 1.0


from pymata4 import pymata4
import time
import random

board = pymata4.Pymata4()

# Constants
TOP_HEIGHT = 10 #cm
maxVehHeight = 4 #cm

# Polling rate
pollingRate = 2 #seconds

#TL6
redPin =13
yellowPin =12
greenPin = 11

#US5
echoPin = 3
triggerPin = 4
# Configuring pins
board.set_pin_mode_sonar(triggerPin,echoPin,timeout=200000)
board.set_pin_mode_digital_output(redPin)
board.set_pin_mode_digital_output(yellowPin)
board.set_pin_mode_digital_output(greenPin)

time.sleep(1)

def heightDiff(distance):
    return TOP_HEIGHT - distance[0]

def normal_state():
    board.digital_pin_write(redPin,1)
    board.digital_pin_write(greenPin,0)
    board.digital_pin_write(yellowPin,0)

def overheight_state_green():
    board.digital_pin_write(redPin,0)
    board.digital_pin_write(greenPin,1)
    time.sleep(5)

def overheight_state_yellow():
    board.digital_pin_write(greenPin,0)
    board.digital_pin_write(yellowPin,1)
    time.sleep(3)
    board.digital_pin_write(yellowPin,0)
    board.digital_pin_write(redPin,1)




def main():
    lastPollTime = time.time()
    normal_state()
    Isgreen= False
    while True:
        try: 

            currentTime = time.time()
            if (currentTime - lastPollTime) >= pollingRate:
                lastPollTime = currentTime
            
                heightUS3 = heightDiff(board.sonar_read(triggerPin)) # height of veh from us3
                print(f"US3 height: {heightUS3:.2f} cm")
                while True:
                    if heightUS3 > maxVehHeight:
                        overheight_state_green()
                        heightUS3 = heightDiff(board.sonar_read(triggerPin)) # height of veh from us3
                        Isgreen= True
                    else:    
                        if Isgreen == True:
                            overheight_state_yellow()
                            Isgreen= False
                            break
                        else:
                            break


        except KeyboardInterrupt:
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()