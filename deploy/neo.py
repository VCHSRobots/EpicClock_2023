from machine import Pin
from neopixel import NeoPixel
import alphabet
import time
import ntptime as ntp
import math
import next_color
import encoder

# c_red = (255, 0, 0)
# c_green = (0, 255, 0)
# c_blue = (0, 0, 255)
# c_black = (0, 0, 0)
# c_white = (255, 255, 255)

# Brightness Reduction
b = .03
c_red   = (int(b*255), 0, 0)
c_green = (0, int(b*255), 0)
c_blue  = (0, 0, int(b*255))
c_black = (0, 0, 0)
c_white = (int(b*255), int(b*255), int(b*255))
c_purple = (int(255),0,int(255))
c_teal = (int(b*0), int(200), int(255))

pin_np = Pin(16, Pin.OUT)
np = NeoPixel(pin_np, 256)
N = 256

def show():
    np.write()

def solid(c):
    for i in range(N): np[i] = c
    
def clear():
    solid((0,0,0))
    
def dim_color(color, dimRatio):
    r, g, b = color
    return (int(r*dimRatio), int(g*dimRatio), int(b*dimRatio))

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
    #print(f"color r {color[0]}, g {color[1]}, b {color[2]}")
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
         
def render_time(hours, mins, sec, isAM, color_digits, color_colon, seconds_color, am_color, brightness):
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
    if hours >= 10: alphabet.render(np, 0, dim_color(color_digits, brightness), str_hours[0])
    alphabet.render(np, 5, dim_color(color_digits, brightness), str_hours[1])
    alphabet.render(np, 9, dim_color(color_colon, brightness), ":")
    alphabet.render(np, 13, dim_color(color_digits, brightness), str_mins[0])
    alphabet.render(np, 19, dim_color(color_digits, brightness), str_mins[1])
    
    partialMin = sec/60*7
    full = int(partialMin)
    remainderFraction = partialMin-full
    #Draw Seconds line
    if(full>0):
        draw_horz_line(7,25,25+full-1, dim_color(seconds_color, brightness))
        draw_horz_line(6,25,25+full-1, dim_color(seconds_color, brightness))
    #Draw partial second 
    set_color(25+full,7,dim_color(dim_color(seconds_color, brightness), remainderFraction))
    set_color(25+full,6,dim_color(dim_color(seconds_color, brightness), remainderFraction))
    
    
    #Draw small 'a'
    draw_horz_line(1, 25, 26, dim_color(am_color, brightness))
    draw_horz_line(2, 25, 26, dim_color(am_color, brightness))
    #Draw small 'm'
    draw_horz_line(1, 28, 30, dim_color(am_color, brightness))
    draw_horz_line(2, 28, 30, dim_color(am_color, brightness))
    #Change the 'a' to a 'p' if it's 'pm'
    if isAM == False:
        set_color(25, 0, dim_color(am_color, brightness)) 
    
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
    solid((5,5,5))
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
            
def rainbow_animation(loops=50, dim_amount = .93, initial_brightness=0.1, speed=56):
    '''Runs a rainbow animation with shifting and dimming effects. Blocks until complete.'''
    
    # Initialize animation
    clear()
    show()
    
    # Initialize color and state
    r, g, b = 255, 0, 20
    state = next_color.ColorStates.BACK_TO_RED
    
    print("Rainbow animation start")
    
    # Draw diagonal lines until reaching the end
    x = 0
    while True:
        draw_line(x, 7, x - 8, -1, dim_color((r, g, b), initial_brightness))
        r, g, b, state = next_color.next_color(r, g, b, state, speed)
        x += 1
        if x > 38:
            break
    
    show()
    
    # Shift horizontally animation
    i = 0
    print("Rainbow animation diagonal complete... starting shift")
    
    while True:
        shift_horizontally()
        show()
        i += 1
        if i > loops or encoder.did_button_press():
            break
    
    # Dim animation
    print("Dim animation")
    current_brightness = dim_amount
    
    while current_brightness > 0.002:
        shift_horizontally()
        show()
        if fade_out(current_brightness) <= 0:
            break
        current_brightness *= dim_amount
    
    print("Rainbow animation complete")
    clear()
    show()

        
    
            
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
    
def shift_pixels_down():
    '''Shifts pixels down the row of NeoPixels.'''
    # Create a temporary list to store the shifted colors
    shifted_pixels = [0] * N

    # Shift the colors down the row
    for i in range(N):
        if i < N - 1:
            shifted_pixels[i] = np[i + 1]
        else:
            shifted_pixels[i] = np[0]
    
    # Update NeoPixels with the shifted colors
    for i in range(N):
        np[i] = shifted_pixels[i]

def shift_horizontally(shift_amount=16):
    '''Shifts pixels horizontally, moving them over one spot to the right. 16 is default because that would move the pixel up 8 rows and then down the 8 in the next column putting the pixel right next to where it started'''
    # Create a temporary list to store the shifted colors
    shifted_pixels = [0] * N

    # Shift the colors by the specified amount to the left
    for i in range(N):
        shifted_pixels[i] = np[i - shift_amount]
    
    # Update NeoPixels with the shifted colors
    for i in range(N):
        np[i] = shifted_pixels[i]

def fade_out(brightness):
    '''Fades out NeoPixels with the specified brightness.'''
    max_color_value = 0
    
    # Dim each pixel's color and update NeoPixels
    for i in range(N):
        dimmed_color = tuple(int(c * brightness) for c in np[i])
        np[i] = dimmed_color
        
        max_color_value = max(max_color_value, max(dimmed_color))
        
    return max_color_value
