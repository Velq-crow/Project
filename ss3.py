# Subsystem 3 Eng1013
# Version: 1.3


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
    """
    Used to minus the distance measured by the ultrasonic sensor (US5) from the TOP_HEIGHT giving the vehicle height.

        Parameters:
            distance: To be used in calculation TOP_HEIGHT - distance[0]

        Returns:
            Returns TOP_HEIGHT - distance[0]
    """
    return TOP_HEIGHT - distance[0]

def normal_state():
    """
    Sets the traffic light (TL6) to red.

        Parameters:
            None

        Returns:
            function has no return
    """
    board.digital_pin_write(redPin,1)
    board.digital_pin_write(greenPin,0)
    board.digital_pin_write(yellowPin,0)

def overheight_state_green():
    """
    Sets the traffic light (TL6) to green.

        Parameters:
            None

        Returns:
            function has no return
    """
    board.digital_pin_write(redPin,0)
    board.digital_pin_write(greenPin,1)
    time.sleep(5)

def overheight_state_yellow():
    """
    Sets the traffic light (TL6) to yellow for the requried time 3 seconds.

        Parameters:
            None

        Returns:
            function has no return
    """
    board.digital_pin_write(greenPin,0)
    board.digital_pin_write(yellowPin,1)
    time.sleep(3)
    board.digital_pin_write(yellowPin,0)
    board.digital_pin_write(redPin,1)

def main():
    """
    The main function that uses the value gained from the heightDiff function and, through if statements,
    triggers different traffic light functions based of the height difference of the overheight vehicle.

        Parameters: 
            None

        Returns:
            function has no return 
    """
    lastPollTime = time.time()
    normal_state()
    isGreen= False
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
                        isGreen= True
                    else:    
                        if isGreen == True: 
                            overheight_state_yellow()
                            isGreen= False
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