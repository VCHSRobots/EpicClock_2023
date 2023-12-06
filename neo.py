from machine import Pin
from neopixel import NeoPixel
import alphabet
import time
import ntptime as ntp

# c_red = (255, 0, 0)
# c_green = (0, 255, 0)
# c_blue = (0, 0, 255)
# c_black = (0, 0, 0)
# c_white = (255, 255, 255)

# Brightness Reduction
b = 0.75
c_red   = (int(b*255), 0, 0)
c_green = (0, int(b*255), 0)
c_blue  = (0, 0, int(b*255))
c_black = (0, 0, 0)
c_white = (int(b*255), int(b*255), int(b*255))

pin_np = Pin(16, Pin.OUT)
np = NeoPixel(pin_np, 256)
N = 256

def show():
    np.write()

def solid(c):
    for i in range(N): np[i] = c
    
def counter():
    hours = 0
    mins = 0
    while True:
        mins += 1
        if mins >= 60:
            mins = 0
            hours += 1
            if hours >= 99: hours = 0
        str_hours = "%02d" % hours
        str_mins  = "%02d" % mins
        solid(c_black)
        c = c_green
        alphabet.render(np, 2, c, str_hours[0])
        alphabet.render(np, 9, c, str_hours[1])
        alphabet.render(np, 14, c, ":")
        alphabet.render(np, 19, c, str_mins[0])
        alphabet.render(np, 26, c, str_mins[1])
        show()
        time.sleep(0.25)
         
def render_time(hours, mins, color_digits, color_colon):
    ''' Writes the time digits to the display. Doesn't clear or show.'''
    err = False
    if hours < 0 or hours > 12: err = True
    if mins < 0 or mins > 59: err = True
    if err:
        str_hours = "--"
        str_mins  = "--"
    else:
        str_hours = "%02d" % hours
        str_mins  = "%02d" % mins
    alphabet.render(np, 2, color_digits, str_hours[0])
    alphabet.render(np, 9, color_digits, str_hours[1])
    alphabet.render(np, 14, color_colon, ":")
    alphabet.render(np, 19, color_digits, str_mins[0])
    alphabet.render(np, 26, color_digits, str_mins[1])

def fill_pattern(pat, color):
    ''' Fills a pattern with given 3-tuple: (start, n, step)'''
    p0, n, step = pat
    for i in range(n):
        indx = p0 + i*step
        if indx >= 0 and indx < N: np[indx] = color
    
def startup_animation():
    ''' Runs a quick startup animation. Blocks till done.'''
    solid((50,50,50))
    show()
    time.sleep(0.3)
    ccs = (c_red, c_blue, c_green)
    square_1 = ((0, 16, 16), (15, 16, 16), (7, 16, 16), (8, 16, 16), (0, 8, 1), (248, 8, 1))
    square_2 = ((14, 15, 16), (17, 15, 16), (9, 15, 16), (22, 15, 16), (9, 6, 1), (241, 6, 1))
    square_3 = ((18, 14, 16), (29, 13, 16), (21, 14, 16), (26, 13, 16), (18, 4, 1), (234, 4, 1))
    square_4 = ((28, 12, 16), (35, 11, 16), (27, 12, 16), (36, 11, 16))
    designs = (square_1, square_2, square_3, square_4)
    for color in ccs:
        for design in designs:
            solid(c_black)
            for seg in design:
                fill_pattern(seg, color)
            show()
            time.sleep(0.2)
            
def blue_square(indx, colon_color = c_blue):
    ''' Shows a blue square to indicate trying to connect to wifi and get time. '''
    solid(c_black)
    square_1 = ((0, 16, 16), (15, 16, 16), (7, 16, 16), (8, 16, 16), (0, 8, 1), (248, 8, 1))
    for seg in square_1: fill_pattern(seg, c_blue)
    if indx > 0:
        ii = indx % 14
        np[ii*16 + 19] = colon_color
        np[ii*16 + 20] = colon_color
    show()
    
    
    
