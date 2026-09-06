from pymata4 import pymata4
import time

board = pymata4.Pymata4()

# --------------------------------
# ULTRASONIC SENSORS
# --------------------------------
US1_TRIG = 2
US1_ECHO = 3

US2_TRIG = 4
US2_ECHO = 5

# --------------------------------
# TL1 LIGHTS
# --------------------------------
TL1_RED = 6
TL1_YELLOW = 7
TL1_GREEN = 8

# --------------------------------
# TL2 LIGHTS
# --------------------------------
TL2_RED = 9
TL2_YELLOW = 10
TL2_GREEN = 11

# --------------------------------
# PA1 BUZZER ENABLE
# (connected to external 555/556)
# --------------------------------
PA1 = 12

# --------------------------------
# OPTIONAL POWER PIN
# --------------------------------
FIVE_VOLT_PIN = 13

# --------------------------------
# SETUP DIGITAL OUTPUTS
# --------------------------------
for pin in range(6, 14):
    board.set_pin_mode_digital_output(pin)

# Turn pin 13 HIGH
board.digital_write(FIVE_VOLT_PIN, 1)

# --------------------------------
# SETUP SONAR
# --------------------------------
board.set_pin_mode_sonar(US1_TRIG, US1_ECHO)
board.set_pin_mode_sonar(US2_TRIG, US2_ECHO)

# --------------------------------
# USER CONFIGURATION
# --------------------------------
try:
    userInput = input(
        "Set Overheight Limit in metres (default 4.0): "
    ).strip()

    setDistance = float(userInput) if userInput else 4.0

except ValueError:
    print("Invalid input. Using default 4.0m")
    setDistance = 4.0

# Convert metres to cm
setHeight = setDistance * 100

# Time threshold for same vehicle
sameVehicleTime = 20

# Last US1 trigger time
lastUS1Detection = 0

# --------------------------------
# TRAFFIC LIGHT FUNCTIONS
# --------------------------------
def tl1_green():
    board.digital_write(TL1_RED, 0)
    board.digital_write(TL1_YELLOW, 0)
    board.digital_write(TL1_GREEN, 1)

def tl1_yellow():
    board.digital_write(TL1_RED, 0)
    board.digital_write(TL1_YELLOW, 1)
    board.digital_write(TL1_GREEN, 0)

def tl1_red():
    board.digital_write(TL1_RED, 1)
    board.digital_write(TL1_YELLOW, 0)
    board.digital_write(TL1_GREEN, 0)

def tl2_green():
    board.digital_write(TL2_RED, 0)
    board.digital_write(TL2_YELLOW, 0)
    board.digital_write(TL2_GREEN, 1)

def tl2_yellow():
    board.digital_write(TL2_RED, 0)
    board.digital_write(TL2_YELLOW, 1)
    board.digital_write(TL2_GREEN, 0)

def tl2_red():
    board.digital_write(TL2_RED, 1)
    board.digital_write(TL2_YELLOW, 0)
    board.digital_write(TL2_GREEN, 0)

# --------------------------------
# START NORMAL STATE
# --------------------------------
tl1_green()
tl2_green()

print("Approach Height Detection System Running")
print(f"Overheight limit set to {setDistance}m")

# --------------------------------
# MAIN LOOP
# --------------------------------
while True:
    print(f"US1 Distance: {distance1} cm | US2 Distance: {distance2} cm")
    # Read sensors
    result1 = board.sonar_read(US1_TRIG)
    result2 = board.sonar_read(US2_TRIG)

    distance1 = result1[0] if result1 and result1[0] > 0 else None
    distance2 = result2[0] if result2 and result2[0] > 0 else None

    # Print sensor distances
    print(f"US1 Distance: {distance1} cm | US2 Distance: {distance2} cm")

    currentTime = time.time()

    # --------------------------------
    # US1 OVERHEIGHT DETECTION
    # --------------------------------
    if distance1 is not None:

        if distance1 < setHeight:

            detectedHeight = round((setHeight - distance1) / 100, 2)

            print("--------------------------------")
            print("OVERHEIGHT VEHICLE DETECTED BY US1")
            print(f"Detected Height Above Limit: {detectedHeight}m")
            print(f"Time: {time.ctime()}")
            print("--------------------------------")

            lastUS1Detection = currentTime

            # Turn buzzer ON
            board.digital_write(PA1, 1)

            # TL1 yellow
            tl1_yellow()
            time.sleep(1)

            # TL1 red
            tl1_red()

            # Hold red 30s
            time.sleep(30)

            # Back to green
            tl1_green()

            # Turn buzzer OFF
            board.digital_write(PA1, 0)

    # --------------------------------
    # US2 OVERHEIGHT DETECTION
    # --------------------------------
    if distance2 is not None:

        if distance2 < setHeight:

            print("--------------------------------")
            print("OVERHEIGHT VEHICLE DETECTED BY US2")
            print(f"Time: {time.ctime()}")
            print("--------------------------------")

            # Turn buzzer ON
            board.digital_write(PA1, 1)

            # Determine same vehicle
            sameVehicle = (
                currentTime - lastUS1Detection
            ) <= sameVehicleTime

            # --------------------------------
            # SAME VEHICLE
            # --------------------------------
            if sameVehicle:

                print("US2 detected SAME vehicle as US1")

                # TL2 yellow
                tl2_yellow()
                time.sleep(1)

                # TL2 red
                tl2_red()

                # Hold red
                time.sleep(30)

                # Return green
                tl2_green()

            # --------------------------------
            # DIFFERENT VEHICLE
            # --------------------------------
            else:

                print("US2 detected DIFFERENT vehicle")

                # Both yellow
                tl1_yellow()
                tl2_yellow()

                time.sleep(1)

                # Both red
                tl1_red()
                tl2_red()

                # Hold red
                time.sleep(30)

                # Return green
                tl1_green()
                tl2_green()

            # Turn buzzer OFF
            board.digital_write(PA1, 0)

    time.sleep(0.2)