from machine import Pin
from neopixel import NeoPixel
import alphabet
import time
import ntptime as ntp
import math

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
    
def clear():
    solid((0,0,0))

def get_xy_index(x, y):
    ''' Returns the index in the neo pixel strip, given an (x,y) location, where (0,0) is the
    bottom left pixel.'''
    # This code assumes the strip is organized as vertical substrips, where the ends of the
    # substrips are joined in an alternating fashon to make one strip in a serpentine manner.
    # It is also assumed that the first pixel is connected at the top left.
    #
    # Therefore if x is even, the pixels run in reverse!
    if x < 0 or x > 31: return -1
    if y < 0 or y > 7: return -1
    n = x * 8 
    if (x % 2) == 0:  n += (7 - y) # We are on a backwards column
    else:             n += y
    return n

def set_color(x, y, color):
    ''' Set color of one pixel at the given x,y location on the grid, where 0,0 is the bottom left.'''
    i = get_xy_index(x, y)
    if i >= 0: np[i] = color

def my_abs(x):
    if x >= 0: return x
    return -x

def draw_line(x0, y0, x1, y1, color):
    ''' Draws a line from x0,y0 to x1,y1 with the given color.'''
    # Uses the DDA (Digital Differential Analyzer) line drawing algorithm
    dx = x1 - x0
    dy = y1 - y0 
    adx = dx 
    ady = dy
    if adx < 0: adx = -adx 
    if ady < 0: ady = -ady 
    if adx > ady: nsteps = adx
    else:         nsteps = ady 
    xinc = dx / float(nsteps)
    yinc = dy / float(nsteps)
    x = float(x0) 
    y = float(y0)
    for i in range(nsteps):
        ix = round(x)
        iy = round(y)
        set_color(round(x), round(y), color)
        x += xinc 
        y += yinc
        
def draw_vert_line(x, y0, y1, color):
    if x < 0 or x > 31: return
    if y0 < y1:
        while True:
            set_color(x, y0, color)
            y0 += 1
            if y0 > y1: return
    else:
        while True:
            set_color(x, y1, color)
            y1 += 1
            if y1 > y0: return
    
    
def draw_horz_line(y, x0, x1, color):
    if y < 0 or y > 7: return
    if x0 < x1:
        while True:
            set_color(x0, y, color)
            x0 += 1
            if x0 > x1: return
    else:
        while True:
            set_color(x1, y, color)
            x1 += 1
            if x1 > x0: return
            
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
    
def show_wifi_ok(color_wifi=c_blue, color_ok=c_green):
    ''' Writes "wifi ok" to the display. Doesn't clear or show.'''
    clear()
    alphabet.render(np, 0, color_wifi, "w")
    alphabet.render(np, 5, color_wifi, "i")
    alphabet.render(np, 9, color_wifi, "f")
    alphabet.render(np, 13, color_wifi, "i")
    alphabet.render(np, 21, color_ok, "o")
    alphabet.render(np, 27, color_ok, "k")
    show()
    
def show_no_wifi(color_no=c_red, color_wifi=c_blue):
    ''' Writes "NO wifi" to the display. Doesn't clear or show.'''
    clear()
    alphabet.render(np,  0, color_no,   "N")
    alphabet.render(np,  6, color_no,   "O")
    alphabet.render(np, 16, color_wifi, "w")
    alphabet.render(np, 21, color_wifi, "i")
    alphabet.render(np, 25, color_wifi, "f")
    alphabet.render(np, 29, color_wifi, "i")
    show()
    
def show_ntp_ok():
    ''' Write "NTP OK" to the dispaly '''
    clear()
    alphabet.new_render("N", 0, c_blue)
    alphabet.new_render("T", 6, c_blue)
    alphabet.new_render("P", 12, c_blue)
    alphabet.new_render("O", 20, c_green)
    alphabet.new_render("k", 26, c_green)
    show()
    
def show_no_ntp():
    ''' Writes "NO NTP" to the display.'''
    clear()
    alphabet.new_render("N", 0, c_red)
    alphabet.new_render("O", 6, c_red)
    alphabet.new_render("N", 14, c_blue)
    alphabet.new_render("T", 20, c_blue)
    alphabet.new_render("P", 26, c_blue)
    show()
    
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
    
    
    
