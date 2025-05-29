# Assignment4.py

# Import required modules for networking, JSON handling, timing, hardware access, and HTTP requests
import network
import ujson
import time
import machine
import urequests
from microdot import Microdot, Response  # Lightweight web framework for microcontrollers

# Constant for configuration file path
CONFIG_FILE = 'config.json'

# Class to control an RGB LED
class RGBLed:
    def __init__(self, red_pin, green_pin, blue_pin):
        # Initialize GPIO pins for red, green, and blue LEDs
        self.red = machine.Pin(red_pin, machine.Pin.OUT)
        self.green = machine.Pin(green_pin, machine.Pin.OUT)
        self.blue = machine.Pin(blue_pin, machine.Pin.OUT)
    def set_color(self, r, g, b):
        self.red.value(r)
        self.green.value(g)
        self.blue.value(b)
    def red_on(self):
        # Turn on red color 
        self.set_color(1, 0, 0)
    def blue_on(self):
        # Turn on blue color 
        self.set_color(0, 0, 1)

    def off(self):
        # Turn off all colors
        self.set_color(0, 0, 0)


# Class to manage loading, saving, and resetting configuration data
class ConfigManager:
    def __init__(self):
        # Default configuration
        self.config = {
            'ssid': '',
            'password': '',
            'api_key': '169MZV28WYEK6NP6'
        }

    def load(self):
        # Load configuration from JSON file if it exists
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.config = ujson.load(f)
            print("Loading configuration:", self.config)
        except:
            print("Configuration not loaded - setting default.")
            self.save()

    def save(self):
        # Save current configuration to JSON file
        with open(CONFIG_FILE, 'w') as f:
            ujson.dump(self.config, f)
        print("Configuration saved.")

    def reset(self):
        # Reset configuration to default values
        self.config = {
            'ssid': '',
            'password': '',
            'api_key': '169MZV28WYEK6NP6'
        }
        self.save()
        print("Configuration has been reset.")


# Class to read sensor data and send it to an IoT service (ThingSpeak)
class IoTClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.adc = machine.ADC(machine.Pin(3))  # Set up ADC on pin 3
        try:
            self.adc.atten(machine.ADC.ATTN_11DB) 
        except:
            pass

    def read_light_level(self):
        # Read analog value from the light sensor
        value = self.adc.read()
        print(f"Measured brightness: {value}")
        return value

    def send_data(self):
        # Send sensor data to ThingSpeak
        value = self.read_light_level()
        url = f'https://api.thingspeak.com/update?api_key={self.api_key}&field1={value}'
        try:
            print("Sending data to ThingSpeak...")
            response = urequests.get(url)
            response.close()
        except:
            print("Error sending data to ThingSpeak.")


# Class to handle WiFi connection to a network
class WiFiConnector:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password

    def connect(self):
        wlan = network.WLAN(network.STA_IF) 
        wlan.active(True)
        wlan.connect(self.ssid, self.password)
        print(f"Connecting to: {self.ssid}")
        for _ in range(15):
            if wlan.isconnected():
                print("WiFi connection was successful.")
                return True
            time.sleep(1)
        print("WiFi did not connect.")
        return False


# Class to host a local WiFi access point with a web server for configuration
class ConfigServer:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.app = Microdot()  # Web server instance
        Response.default_content_type = 'text/html'  # Default response type
        self.create_routes()  # Define web routes
        self.ap = network.WLAN(network.AP_IF)  # Access Point interface

    def create_routes(self):
        # Define the index route (main page)
        @self.app.route('/')
        def index(req):
            try:
                with open('Assigment4/templates/index.html') as f:
                    return f.read()
            except:
                return "Could not load index.html"

        # Serve the CSS file
        @self.app.route('/style.css')
        def style(req):
            try:
                with open('Assigment4/templates/style.css') as f:
                    return Response(body=f.read(), content_type='text/css')
            except:
                return "Could not load style.css", 404

        # Handle form submission to save config
        @self.app.route('/save', methods=['POST'])
        def save_config(req):
            # Extract submitted values
            ssid = req.form.get('ssid', '')
            password = req.form.get('password', '')
            api_key = req.form.get('api_key', '')

            # Update configuration and save it
            self.config_manager.config['ssid'] = ssid
            self.config_manager.config['password'] = password
            self.config_manager.config['api_key'] = api_key
            self.config_manager.save()

            # Restart device after saving
            print("Saving and restarting.")
            self.ap.active(False)
            time.sleep(1)
            machine.reset()
            return "Saving and restarting."

    def start(self):
        # Start the access point for configuration
        ssid = "Config-Device"
        password = "12345678"
        self.ap.active(True)
        self.ap.config(essid=ssid, password=password)
        ip = self.ap.ifconfig()[0]
        print(f"Launched AP: {ssid} | IP: {ip}")
        self.app.run(host='0.0.0.0', port=80)  # Start web server

