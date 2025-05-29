#Author Samuel Fáber 5ZYS21

# Import necessary modules and classes from the Assigment4 package
from Assignment4.Assignment4 import (
    ConfigManager,    # Handles loading, saving, and resetting configuration
    RGBLed,           # Controls an RGB LED
    IoTClient,        # Sends data to an IoT server
    WiFiConnector,    # Manages WiFi connection
    ConfigServer      # Hosts a configuration server for setting WiFi credentials
)
import machine         # Provides access to hardware features of the microcontroller
import time            # Allows time-based operations like delays

def main():
    print("Starting the program")
    
    # Load stored configuration
    config = ConfigManager()
    config.load()

    # Initialize RGB LED with specific GPIO pins
    rgb = RGBLed(red_pin=10, green_pin=11, blue_pin=21)
    
    # Initialize button input on pin 2 with pull-up resistor
    button = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)

    # Check if button is pressed or configuration is incomplete
    if button.value() == 0 or not config.config['ssid'] or not config.config['password']:
        print("Configuration mode is active.")
        rgb.blue_on()        # Turn on blue LED to indicate config mode
        config.reset()       # Clear existing configuration
        server = ConfigServer(config)  # Start configuration server
        server.start()
        return               # Exit the function to stop further execution

    # Try connecting to WiFi using the loaded configuration
    wifi = WiFiConnector(config.config['ssid'], config.config['password'])
    if wifi.connect():
        print("IoT mode is active.")
        rgb.red_on()         # Turn on red LED to indicate IoT mode is active
        client = IoTClient(config.config['api_key'])

        while True:
            # If button is pressed during IoT operation, switch to config mode
            if button.value() == 0:
                print("Entering configuration mode")
                rgb.blue_on()
                config.reset()
                time.sleep(1)
                machine.reset()  # Restart the device to re-enter config mode

            client.send_data()   # Send data to the IoT platform
            time.sleep(1)        # Wait before sending next data packet
    else:
        # If WiFi connection fails, enter configuration mode
        print("WiFi failed - entering configuration mode..")
        rgb.blue_on()
        server = ConfigServer(config)
        server.start()

# Run the main function
main()
    
