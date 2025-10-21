import time
import random
import RPi.GPIO as GPIO
from shifter import Shifter

class Bug:
    def __init__(self, timestep=0.1, x=3, isWrapOn=False):
        self.timestep = timestep      
        self.x = x                    
        self.isWrapOn = isWrapOn      
        self.__shifter = Shifter(23, 24, 25)
        self._running = False

    def step(self, timestep=None):
        if not self._running:
            return

        if timestep is None:
            timestep = self.timestep

        pattern = 1 << self.x # lights up LED at position
        self.__shifter.shiftByte(pattern)

        self.x += random.choice([-1, 1]) # randomly moves bug left or right

        if self.isWrapOn:
            self.x %= 8
        else:
            self.x = max(0, min(7, self.x))

        time.sleep(timestep)

    def start(self):
        self._running = True

    def stop(self):
        self._running = False
        self.__shifter.shiftByte(0b00000000)


dataPin = 23
latchPin = 24
clockPin = 25

switch1 = 16 # start/stop switch
switch2 = 20 # wrap switch
switch3 = 21 # speed switch

GPIO.setmode(GPIO.BCM)
for pin in [switch1, switch2, switch3]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

bug = Bug()

def toggle_wrap(channel): # flips wrap mode on and off
    bug.isWrapOn = not bug.isWrapOn
    print(f"Wrap mode toggled: {bug.isWrapOn}")

GPIO.add_event_detect(switch2, GPIO.RISING, callback=toggle_wrap, bouncetime=300) # detects switch 2

try:
    while True:
        if GPIO.input(switch1): # control the start and stop
            if not bug._running:
                bug.start()
        else:
            if bug._running:
                bug.stop()

        current_step = bug.timestep / 3 if GPIO.input(switch3) else bug.timestep # makes bug 3x faster

        bug.step(current_step) # move bug one step

except KeyboardInterrupt:
    bug.stop()
    GPIO.cleanup()
