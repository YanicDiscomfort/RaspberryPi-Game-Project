# PCF8591        Raspberry Pi
# --------       ------------
# VCC      <-->  3.3V (Pin 1)
# GND      <-->  GND (Pin 6)
# SDA      <-->  SDA (GPIO 2, Pin 3)
# SCL      <-->  SCL (GPIO 3, Pin 5)
# AIN0     <-->  VRX (Joystick)


# Raspberry     LED
# ---------     ---
# 34 GND    <-> - Bar
# 11 GPIO17 <-> - LED
# 13 GPIO27 <-> - LED
# 15 GPIO22 <-> - LED



# Set the GPIO mode to BCM



#try:
#    while True:
#        # Read the analog value from the joystick's VRX pin (channel 0)
#        vrx_value = read_adc(0)
#        if vrx_value is not None:
#            if vrx_value < 100:
#                print("Joystick moved to the left")
#            elif vrx_value > 225:
#                print("Joystick moved to the right")
#            else:
#                print("Joystick is idle")
#        time.sleep(0.1)  # Wait for 100 milliseconds before reading again
#except KeyboardInterrupt:
    # Clean up GPIO settings before exiting
#    GPIO.cleanup()
