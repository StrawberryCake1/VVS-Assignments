from machine import Pin, PWM
import time
import music.music_test
"""
Author: Samuel Fáber 5ZYS21
Date: 29.03.2025
Used port COM10
I had a problem with melodies so in music/music_test I had to make my own method I was repairing it with Mr.Bača4
def play(melodyNumber, volume_intensity):
    set_volume(volume_intensity)
    playsong(playsong(melody[melodyNumber]))
"""
#Class button for changing volume by pressing the button
class Button:
    def __init__(self):
        self.x = 0
        self.button = Pin(2, Pin.IN, Pin.PULL_UP)
    def pressed(self):
        """
        Method pressed is checking if button is pressed by button value if button.value() == 0
        then self.x is changed so melody can be changed
        """
        while True:
            if self.x > 9:
                self.x = 0
                # Debounce
            if self.button.value() == 0:#Volume = 0
                self.x += 1
                print("button pressed volume changed")
                time.sleep(2)
                break
    def getX(self):
        return self.x
#RGBLed class for choosing 1 of 7 colors and also for smooth color transition
class RGBLed:
    def __init__(self, r_pin=21, g_pin=11, b_pin=10):
        self.r = PWM(Pin(r_pin), freq=1000, duty=0)
        self.g = PWM(Pin(g_pin), freq=1000, duty=0)
        self.b = PWM(Pin(b_pin), freq=1000, duty=0)
#Method for setting LED colors by parameter
    def set_color(self, red, green, blue):
        #Set LED brightness for red, green, and blue (0-255 --> 0-1023 PWM)
        self.r.duty(int(red * 1023 / 255))
        self.g.duty(int(green * 1023 / 255))
        self.b.duty(int(blue * 1023 / 255))
    def fade_effect(self, duration):
        # List of colors for smooth transitions
        colors = [
            (255, 0, 0), # Red
            (255, 255, 0), # Yellow
            (0, 255, 0), # Green
            (255, 0, 255), # Magenta
            (0, 0, 255), # Blue
            (0, 255, 255), # Cyan
            (255, 0, 0) #Red again
        ]
        steps = 100
        # Calculate delay for each step to match the total duration
        delay = duration * 1000 / (len(colors) * steps)
        # Loop through each color transition
        for i in range(len(colors) - 1):
            # Gradually change colors in small steps
            for step in range(steps):
                # Calculate new red, green, and blue values
                r = colors[i][0] + (colors[i + 1][0] - colors[i][0]) * step / steps
                g = colors[i][1] + (colors[i + 1][1] - colors[i][1]) * step / steps
                b = colors[i][2] + (colors[i + 1][2] - colors[i][2]) * step / steps
                # Set the new color on the LED
                self.set_color(r, g, b)
                # Short delay for smooth transition
                time.sleep_ms(int(delay))

#Class PlayMusic for playing 1 of 5 melodies
class PlayMusic:
    def __init__(self):
            self.melody = None
            self.volume_intensity = None
    def change_melody(self, melody):
        self.melody = melody
    def change_intensity(self, volume_intensity):
        self.volume_intensity = volume_intensity
    def play_music(self):
        music.music_test.play(self.melody, self.volume_intensity)
    """
    Parameter of this method is parameter choosed by user.Switch respectively match will choose the real number
    of a melody from melodies.py file
    """
    def melody_selector(self, selection):
        if selection == 1:
            return 2
        elif selection == 2:
            return 9
        elif selection == 3:
            return 37
        elif selection == 4:
            return 19
        elif selection == 5:
            return 23
        else:
            print("Wrong input !Choose numbers between 1-5 !")
            return None
#Class Application to interact with the user by choosing 1 of valid options
class Application:
    def __init__(self):
        #Instance of RGBLed class
        self.led = RGBLed(r_pin=21, g_pin=11, b_pin=10)
        self.colors = {
            '1': (255, 0, 0),  # red
            '2': (0, 255, 0),  # green
            '3': (0, 0, 255),  # blue
            '4': (255, 255, 0),  # yellow
            '5': (255, 0, 255),  # purple
            '6': (0, 255, 255),  # azure
            '7': (255, 255, 255)  # white
        }
        # Instance of PlayMusic class
        self.music_player = PlayMusic()
        # Instance of Button class
        self.button = Button()

    def run(self):
        print("****************************************")
        print("Assigment one RGBLED+BUZZER")
        print("Options:")
        print("1-7: Light up one of 7 colors: (red, green, blue, yellow, purple, azure, white)" )
        print("f: Start color transition effect (1-5 seconds)")
        print("m: Play one of 5 melodies")
        print("v: change volume by pressing button")
        print("q: Exit the program")
        while True:
            #User is selecting on of displayed commands
            print("****************************************")
            command = input("Select command: ")
            #If user input is 1-7 one of the LEDs lights up
            if command in self.colors:
                self.led.set_color(*self.colors[command])
                print(f"Currently displayed color is: {command}")
            elif command == 'f':
                try:
                    print("****************************************")
                    print("Color transition effect")
                    duration1 = float(input("Enter the effect length (1-5 seconds): "))
                    #If druation is < than 1 duration will be 1
                    #If duration is > 5 than duration will be 5
                    duration = max(1, min(5, duration1))
                    self.led.fade_effect(duration)
                except ValueError:
                    print("Invalid effect length !")
            elif command == 'm':
                try:
                    print("****************************************")
                    print("Melody selection")
                    print("1: Pacman")#2
                    print("2: Nokia ringtone")#9
                    print("3: Super Mario Bros theme")#37
                    print("4: At Doom´s gate")#19
                    print("5: Marry Christmas")#2
                    melody = int(input("Write one of melodies: 1-5 "))
                    #Changnig melody using melody selector
                    self.music_player.change_melody(self.music_player.melody_selector(melody))
                    #Changing intensity to number of pressed button * 6400 (32000/10 == 3200)
                    self.music_player.change_intensity(self.button.getX() * 3200)
                    self.music_player.play_music()
                except ValueError:
                    print("Invalid effect length !")
            elif command == 'v':
                print("****************************************")
                print("Current volume level: ", self.button.getX(), (self.button.getX() * 3200))
                print("Press button to change volume (1-5)")
                self.button.pressed()
            elif command == 'q':
                print("****************************************")
                print("Shutting down program...")
                print("****************************************")
                break
            else:
                print("****************************************")
                print("Bad input !")
