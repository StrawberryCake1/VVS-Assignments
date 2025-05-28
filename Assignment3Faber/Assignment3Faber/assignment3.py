from machine import Pin, PWM, ADC
import network
import socket
import time
import neopixel
import music.music_test
from machine import lightsleep, wake_reason
import esp32


# Class to interface with a photoresistor using ADC
class Photoresistor:
    def __init__(self, pin_num):
        self.sensor = ADC(Pin(pin_num))
        self.sensor.atten(ADC.ATTN_11DB)  # Set input voltage range to 0-3.3V

    def read_value(self):
        return self.sensor.read()


# Class for controlling a regular RGB LED using PWM on 3 pins
class RGBLed:
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red = PWM(Pin(red_pin), freq=1000, duty=0)
        self.green = PWM(Pin(green_pin), freq=1000, duty=0)
        self.blue = PWM(Pin(blue_pin), freq=1000, duty=0)

    def set_color(self, r, g, b):
        # Scale values (0–255) to PWM duty cycle (0–1023)
        self.red.duty(int(r * 1023 / 255))
        self.green.duty(int(g * 1023 / 255))
        self.blue.duty(int(b * 1023 / 255))


# Class for controlling serial RGB LEDs (NeoPixels)
class SerialRGBLed:
    def __init__(self, pin_num, count):
        self.np = neopixel.NeoPixel(Pin(pin_num), count)
        self.count = count

    def set_color(self, index, r, g, b):
        if index == 0:
            self.np.fill((r, g, b))  # Set all LEDs to the same color
        elif 0 < index <= self.count:
            self.np[index - 1] = (r, g, b)  # Set color of specific LED

    def apply(self):
        self.np.write()  # Apply changes to LEDs


# Class for handling the piezo buzzer using PWM
class Buzzer:
    def __init__(self, pin_num):
        self.pwm = PWM(Pin(pin_num))
        self.pwm.freq(2000)  # Set tone frequency
        self.pwm.duty(0)     # Start with sound off

    def control(self, state):
        self.pwm.duty(512 if state == "on" else 0)  # 50% duty cycle for sound


# Class for playing predefined melodies with variable volume
class PlayMusic:
    def __init__(self):
        self.melody = None
        self.volume_intensity = None

    def change_melody(self, melody_name):
        melodies = {
            "pacman": 2,
            "nokia": 9,
            "mario": 37,
            "doom": 19,
            "xmas": 23
        }
        self.melody = melodies.get(melody_name)

    def change_intensity(self, volume_intensity):
        self.volume_intensity = volume_intensity

    def play_music(self):
        if self.melody is not None:
            music.music_test.play(self.melody, self.volume_intensity)


# Main controller for device functionalities
class DeviceController:
    def __init__(self):
        self.photoresistor = Photoresistor(3)
        self.rgb_led = RGBLed(21, 11, 10)
        self.serial_led = SerialRGBLed(8, 3)  
        self.buzzer = Buzzer(5)
        self.music_player = PlayMusic()
        self.ap_ssid = "ESP32C6-Faber"
        self.ap_password = "123456"
        self.interval_ms = 300
        self.ap = None

    # Set up ESP32 as a Wi-Fi access point
    def setup_ap(self):
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(True)
        self.ap.config(essid=self.ap_ssid, password=self.ap_password)
        while not self.ap.active():
            time.sleep(0.1)
        print("AP setup complete. IP:", self.ap.ifconfig()[0])

    # Put the device into light sleep mode for given seconds or until button press
    def enter_light_sleep(self, seconds):
        wake_pin = Pin(0, Pin.IN, Pin.PULL_UP)  # Use GPIO0 as wake-up pin
        esp32.wake_on_ext0(pin=wake_pin, level=esp32.WAKEUP_ALL_LOW)

        ms = int(seconds * 1000)
        print(f"ESP32 is in lightsleep for {seconds} seconds...")
        lightsleep(ms)
        print("ESP32 woke up!")

    # Process incoming HTTP request from web client
    def handle_request(self, conn):
        request = conn.recv(1024).decode()
        print("Request received:", request)
        try:
            req_line = request.split('\r\n')[0]
            method, path, _ = req_line.split(' ')
        except:
            conn.close()
            return

        if path == '/' or path == '/index.html':
            response = self.serve_home()
        elif path == '/style.css':
            response = self.serve_css()
        elif path == '/value':
            value = self.photoresistor.read_value()
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{value}"
        elif path == '/control' and method == 'POST':
            data = request.split('\r\n\r\n')[1]
            params = {}
            for pair in data.split('&'):
                if '=' in pair:
                    key, value = pair.split('=')
                    params[key] = value

            # RGB color change
            if 'red' in params or 'green' in params or 'blue' in params:
                r = int(params.get('red', 0))
                g = int(params.get('green', 0))
                b = int(params.get('blue', 0))
                self.rgb_led.set_color(r, g, b)

            # Buzzer on/off
            if 'buzzer' in params:
                self.buzzer.control(params.get('buzzer', 'off'))

            # Serial LED control
            if 'sindex' in params:
                idx = int(params.get('sindex', 0))
                r = int(params.get('sred', 0))
                g = int(params.get('sgreen', 0))
                b = int(params.get('sblue', 0))
                self.serial_led.set_color(idx, r, g, b)
                self.serial_led.apply()

            response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

        elif path == '/melody' and method == 'POST':
            data = request.split('\r\n\r\n')[1]
            params = {}
            for pair in data.split('&'):
                if '=' in pair:
                    key, value = pair.split('=')
                    params[key] = value

            melody = params.get('melody', '')
            volume = int(params.get('volume', 16000))
            self.music_player.change_melody(melody)
            self.music_player.change_intensity(volume)
            self.music_player.play_music()
            response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\nPage not found"

        conn.send(response)
        conn.close()

    # Serve index.html from local file system
    def serve_home(self):
        try:
            with open('Application/templates/index.html', 'r') as f:
                html = f.read()
            return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
        except Exception as e:
            print("HTML loading error:", e)
            return "HTTP/1.1 500 Internal Server Error\r\n\r\nError loading HTML"

    # Serve CSS file
    def serve_css(self):
        try:
            with open('Application/templates/style.css', 'r') as f:
                css = f.read()
            return f"HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n\r\n{css}"
        except Exception as e:
            print("CSS loading error:", e)
            return "HTTP/1.1 500 Internal Server Error\r\n\r\nError loading CSS"

    # Start the socket server
    def start_server(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        sock = socket.socket()
        sock.bind(addr)
        sock.listen(1)
        print("Server started on", addr)
        while True:
            conn, addr = sock.accept()
            print("Client connected from", addr)
            self.handle_request(conn)

    # Main entry point for the program
    def run(self):
        try:
            seconds = int(input("Set time in seconds for lightsleep: "))
        except:
            seconds = 5  # Default fallback
        self.enter_light_sleep(seconds)
        self.setup_ap()
        self.start_server()

