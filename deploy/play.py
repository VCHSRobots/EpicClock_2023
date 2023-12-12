from machine import Pin
from neopixel import NeoPixel
import time

c_red = (255, 0, 0)
c_green = (0, 255, 0)
c_blue = (0, 0, 255)
c_black = (0, 0, 0)
c_white = (255, 255, 255)

pin_np = Pin(16, Pin.OUT)
np = NeoPixel(pin_np, 256)
N = 256

def show():
    np.write()

def solid(c):
    for i in range(N): np[i] = c

def chase():
    i = 0
    while True:
        i += 1
        if i >= N: i = 0
        solid(c_black)
        np[i] = c_white
        show()
        time.sleep(0.025)

def rgb():
    while True:
        solid(c_red)
        show()
        time.sleep(1.0)
        solid(c_green)
        show()
        time.sleep(1.0)
        solid(c_blue)
        show()
        time.sleep(1.0)


    
        