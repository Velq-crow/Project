# Subsystem 4 Eng1013
# Version: 1.3


from pymata4 import pymata4
import time
import random

board = pymata4.Pymata4()

# Constants
TOP_HEIGHT = 10 #cm

# Polling rate
pollingRate = 2 #seconds

#TL3 
redPin = 2
greenPin = 3

#US3
triggerPinUS3 = 9
echoPinUS3 = 6

#US4
triggerPinUS4 = 8
echoPinUS4 = 7
acceptableError = 30 # percentage error when cross checking

# Configuring pins for TL3
board.set_pin_mode_digital_output(redPin)
board.set_pin_mode_digital_output(greenPin)

# Configuring pins for US3 and US4
board.set_pin_mode_sonar(triggerPinUS3,echoPinUS3,timeout=200000)
board.set_pin_mode_sonar(triggerPinUS4,echoPinUS4,timeout=200000)

# sleep to configure pins
time.sleep(1)

def heightDiff(distance):
    """
    Used to minus the distance measured by the ultrasonic sensor (US5) from the TOP_HEIGHT to give actual height of the vechicle.

        Parameters:
            distance: To be used in calculation TOP_HEIGHT - distance[]

        Returns:
            Returns TOP_HEIGHT - distance[0]
    """
    return TOP_HEIGHT - distance[0]
    
def normal_state():
    """
    This switches the pin connected to the green LED to 1 to allow traffic to flow through to the tunnel.

        Parameters:
            None

        Returns:
            This function has no returns
    """
    board.digital_pin_write(redPin,0)
    board.digital_pin_write(greenPin,1)

def overheight_state():
    """
    This switches the pin connected to the red LED to 1 to shine red and stop the overheight vehicle from moving into the tunnel.

        Parameters:
            None

        Returns:
            This function has no returns
    """
    board.digital_pin_write(redPin,1)
    board.digital_pin_write(greenPin,0)

def shutdown_state():
    """
    Switches all traffic light pins to 0 in turn shutting down all traffic LEDs.

        Parameters:
            None

        Returns:
            This function has no returns
    """
    board.digital_pin_write(redPin,0)
    board.digital_pin_write(greenPin,0)

def main():
    """ 
    The main function, that is the central control loop that continuously polls ultrasonic sensors to measure the 
    height of the vehicle and manage traffic light states based the vehicle's height. 

        Parameters:
            None

        Returns: 
            This function has no returns
    """
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

            lastPollTime = time.time()
            while True:
                currentTime = time.time()
                if (currentTime - lastPollTime) >= pollingRate:
                    lastPollTime = currentTime

                    heightUS3 = heightDiff(board.sonar_read(triggerPinUS3)) # height of veh from us3
                    heightUS4 = heightDiff(board.sonar_read(triggerPinUS4)) # height of veh from us4

                    lowerErrorBound = heightUS3*(1- acceptableError/100)
                    upperErrorBound = heightUS3*(1+ acceptableError/100)

                    print(f"US3 height: {heightUS3:.2f} cm \n US4 height: {heightUS4:.2f} cm")

                    if heightUS3 >= overHeightLimit:
                        if lowerErrorBound <= heightUS4 <= upperErrorBound:
                            overheight_state()
                    else:
                            normal_state()
                    
                time.sleep(0.05)

        except KeyboardInterrupt:
            shutdown_state()
            print("\nExiting program")
            time.sleep(1)
            break

    board.shutdown()
if __name__ == "__main__":
    main()



