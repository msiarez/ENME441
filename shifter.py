import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

class Shifter:
	def __init__(self, dataPin, latchPin, clockPin):
        self.dataPin = dataPin
        self.latchPin = latchPin
        self.clockPin = clockPin
        GPIO.setup(self.dataPin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.latchPin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.clockPin, GPIO.OUT, initial=GPIO.LOW)

    def _ping(self, pin):
    	GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.00001)

    def shiftByte(self, pattern):
        for i in range(8):
            GPIO.output(self.dataPin, (pattern >> i) & 1)
            self._ping(self.clockPin)
        self._ping(self.latchPin)
