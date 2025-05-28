import sys
import time
from machine import Pin, ADC, PWM, Timer, UART
import neopixel


class LightUpLeds:
    """Class to control a strip of NeoPixel RGB LEDs."""

    def __init__(self, pin_number: int) -> None:
        """Initialize the NeoPixel strip on the given pin."""
        self.pin = Pin(pin_number, Pin.OUT)
        self.np = neopixel.NeoPixel(self.pin, 3)

    def set_color(self, index: int, r: int, g: int, b: int) -> None:
        """Set the color of the NeoPixel at a specific index."""
        self.np[index] = (r, g, b)
        self.np.write()


class ChangeColor:
    """Class to change the RGB LED color based on photoresistor brightness."""
    def __init__(
        self,
        photo_pin: int = 3,
        red_pin: int = 21,
        green_pin: int = 11,
        blue_pin: int = 10,
        interval_ms: int = 300,
    ) -> None:
        """Initialize components and start brightness-based color updates."""
        self.photoresistor = ADC(Pin(photo_pin))
        self.photoresistor.atten(ADC.ATTN_11DB)

        self.red_pwm = PWM(Pin(red_pin), freq=1000)
        self.green_pwm = PWM(Pin(green_pin), freq=1000)
        self.blue_pwm = PWM(Pin(blue_pin), freq=1000)

        self.timer = Timer(0)
        self.timer.init(
            period=interval_ms,
            mode=Timer.PERIODIC,
            callback=self.update_color
        )

        time.sleep(10)
        self.timer.deinit()
        self.set_color(0, 0, 0)

    def set_color(self, r: int, g: int, b: int) -> None:
        """Set RGB LED brightness (0-1023 per channel)."""
        self.red_pwm.duty(int(r))
        self.green_pwm.duty(int(g))
        self.blue_pwm.duty(int(b))

    def update_color(self, t: Timer) -> None:
        """Update LED color based on photoresistor brightness."""
        light_value = self.photoresistor.read()
        brightness = light_value / 4095

        if brightness < 0.25:
            r, g, b = 1023, 0, 0
        elif brightness < 0.5:
            r, g, b = 0, 1023, 0
        elif brightness < 0.75:
            r, g, b = 0, 0, 1023
        else:
            r, g, b = 1023, 1023, 1023

        self.set_color(r, g, b)


class Communication:
    """Class for UART-based communication (TX, RX, Node modes)."""
    def __init__(self) -> None:
        """Initialize UART for communication."""
        self.uart = UART(1, 9600, tx=Pin(15), rx=Pin(23))

    def transmitter(self) -> None:
        """Send user input over UART."""
        print("Mode: TRANSMITTER")
        while True:
            try:
                data = input("Enter message to send: ")
                if data == "exit":
                    break
                self.uart.write(data + '\n')
            except KeyboardInterrupt:
                print("\nTransmitter stopped.")
                break

    def transmitter_and_reciever(self) -> None:
        """Forward received UART messages (node mode)."""
        print("Mode: NODE (forwarding data)")
        while True:
            try:
                if self.uart.any():
                    data = self.uart.readline()
                    if data:
                        self.uart.write(data)
            except KeyboardInterrupt:
                print("\nNode stopped.")
                break

    def receiver(self) -> None:
        """Receive and print UART messages."""
        print("Mode: RECEIVER")
        while True:
            try:
                if self.uart.any():
                    data = self.uart.readline()
                    if data:
                        print("Received:", data.decode().strip())
            except KeyboardInterrupt:
                print("\nReceiver stopped.")
                break


def run_program() -> None:
    """Main control function providing menu-driven interaction."""
    while True:
        try:
            print("**************************************************")
            print("[1] Light up RGB NeoPixels")
            print("[2] Light-sensitive RGB diode")
            print("[3] UART communication")
            print("[exit] Exit program")

            option = input("Choose 1 option: ")
            if option == "exit":
                print("Exiting the program...")
                break

            option = int(option)

            if option == 1:
                led_color = input("Color of the LED (red, green, blue, yellow, purple, azure, white): ")
                number_of_leds = int(input("Number of LEDs (1-3): "))
                light_up_leds = LightUpLeds(8)

                colors = {
                    "red": (255, 0, 0),
                    "green": (0, 255, 0),
                    "blue": (0, 0, 255),
                    "yellow": (255, 255, 0),
                    "purple": (255, 0, 255),
                    "azure": (0, 255, 255),
                    "white": (255, 255, 255)
                }

                if led_color in colors:
                    for i in range(number_of_leds):
                        light_up_leds.set_color(i, *colors[led_color])
                    time.sleep(5)
                    for i in range(number_of_leds):
                        light_up_leds.set_color(i, 0, 0, 0)
                else:
                    print("Wrong color!")

            elif option == 2:
                ChangeColor()

            elif option == 3:
                print("Select mode:")
                print("[1] - Transmitter")
                print("[2] - Transmitter and Receiver")
                print("[3] - Receiver")
                mode = input("Enter mode number: ")
                comm = Communication()

                if mode == "1":
                    comm.transmitter()
                elif mode == "2":
                    comm.transmitter_and_reciever()
                elif mode == "3":
                    comm.receiver()
                else:
                    print("Invalid mode selected.")

            else:
                print("Wrong input!")

        except ValueError as e:
            print("Invalid input:", e)

