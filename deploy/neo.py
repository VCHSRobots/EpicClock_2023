from machine import Pin
from neopixel import NeoPixel
#from main import RenderStyles
import alphabet
import time
import ntptime as ntp
import math
import next_color
import encoder
import render_styles as RenderStyles


# c_red = (255, 0, 0)
# c_green = (0, 255, 0)
# c_blue = (0, 0, 255)
# c_black = (0, 0, 0)
# c_white = (255, 255, 255)

# Brightness Reduction
b = .03
c_red   = (255, 0, 0)
c_green = (0, 255, 0)
c_blue  = (0, 0, 255)
c_black = (0, 0, 0)
c_white = (255, 255, 255)
c_purple = (255,0,255)
c_teal = (0, 200, 255)

pin_np = Pin(16, Pin.OUT)
np = NeoPixel(pin_np, 256)
N = 256
PANEL_WIDTH = 32
PANEL_HEIGHT = 8
CHAR_WIDTH = 6

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
         
#     SHORT_SECOND_LINE = 0
#     LONG_SECOND_LINE = 1
#     NUMBERED_SECONDS = 2
#     BORRING_MODE = 3
         
def render_time(hours, mins, sec, isAM, color_digits, color_colon, seconds_color, am_color, brightness, render_style = RenderStyles.NUMBERED_SECONDS):
    ''' Writes the time digits to the display. Doesn't clear or show.'''
    if render_style == RenderStyles.BORING_MODE:
        digit_column = [3,9,13,17,23]
    else: digit_column = [0,5,9,13,19]
    
    err = False
    if hours < 0 or hours > 12: err = True
    if mins < 0 or mins > 59: err = True
    if err:
        str_hours = "--"
        str_mins  = "--"
    else:
        str_hours = "%02d" % hours
        str_mins  = "%02d" % mins
    if hours >= 10 or render_style == RenderStyles.BORING_MODE: alphabet.render(np, digit_column[0], dim_color(color_digits, brightness), str_hours[0])
    
    alphabet.render(np, digit_column[1], dim_color(color_digits, brightness), str_hours[1])
    alphabet.render(np, digit_column[2], dim_color(color_colon, brightness), ":")
    alphabet.render(np, digit_column[3], dim_color(color_digits, brightness), str_mins[0])
    alphabet.render(np, digit_column[4], dim_color(color_digits, brightness), str_mins[1])

    if render_style == RenderStyles.SHORT_SECOND_LINE:  
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
        draw_am_pm(isAM, am_color, brightness)
    elif render_style == RenderStyles.LONG_SECOND_LINE:
        partialMin = sec/60*32
        full = int(partialMin)
        remainderFraction = partialMin-full
        #Draw Seconds line
        if(full>0):
            draw_horz_line(7,0,full-1, dim_color(seconds_color, brightness))
            set_color(full,7,dim_color(dim_color(seconds_color, brightness), remainderFraction))
        draw_am_pm(isAM, am_color, brightness)
    elif render_style == RenderStyles.NUMBERED_SECONDS:
        alphabet.render_char(get_char_at_index(sec,1),25,dim_color(seconds_color, brightness), size='3x5')
        alphabet.render_char(get_char_at_index(sec,0),29,dim_color(seconds_color, brightness), size='3x5')

        

    
    
def get_char_at_index(number, index):
    # Convert the number to a string
    number_str = str(number)
    
    # Reverse the string
    reversed_str = ''.join(reversed(number_str))
    
    # Check if the index is within the range of the reversed string
    if index >= 0 and index < len(reversed_str):
        # Get the character at the specified index
        return reversed_str[index]
    else:
        # Index out of range
        return '0'
    
def draw_am_pm(isAM, am_color, brightness):
   #Change the 'a' to a 'p' if it's 'pm'
    if isAM:
        #Draw 'a'
        draw_horz_line(0, 25, 27, dim_color(am_color, brightness))
        draw_horz_line(1, 25, 27, dim_color(am_color, brightness))
        draw_horz_line(2, 26, 27, dim_color(am_color, brightness))
    else:
        #Draw 'p'
        draw_horz_line(1, 25, 27, dim_color(am_color, brightness))
        draw_horz_line(2, 25, 27, dim_color(am_color, brightness))
        set_color(25, 0, dim_color(am_color, brightness)) 
    #Draw 'm'
    draw_vert_line(29, 0, 2, dim_color(am_color, brightness))
    draw_vert_line(30, 1, 2, dim_color(am_color, brightness))
    draw_vert_line(31, 0, 2, dim_color(am_color, brightness))
def show_wifi_ok(ip_address, color_wifi=c_blue, color_ok=c_green):
    ''' Writes "wifi ok" to the display. Doesn't clear or show.'''
    clear()
    alphabet.render(np, 0, dim_color(color_wifi, b), "w")
    alphabet.render(np, 5, dim_color(color_wifi, b), "i")
    alphabet.render(np, 9, dim_color(color_wifi, b), "f")
    alphabet.render(np, 13, dim_color(color_wifi, b), "i")
    alphabet.render(np, 21, dim_color(color_ok, b), "o")
    alphabet.render(np, 27, dim_color(color_ok, b), "k")
    show()
    time.sleep(.5)
    
    scroll_text(ip_address,dim_color(color_wifi, b), .005)
    
def show_no_wifi(color_no=c_red, color_wifi=c_blue):
    ''' Writes "NO wifi" to the display. Doesn't clear or show.'''
    clear()
    alphabet.render(np,  0, dim_color(color_no, b),   "N")
    alphabet.render(np,  6, dim_color(color_no, b),   "O")
    alphabet.render(np, 16, dim_color(color_wifi, b), "w")
    alphabet.render(np, 21, dim_color(color_wifi, b), "i")
    alphabet.render(np, 25, dim_color(color_wifi, b), "f")
    alphabet.render(np, 29, dim_color(color_wifi, b), "i")
    show()
    
def show_ntp_ok():
    ''' Write "NTP OK" to the dispaly '''
    clear()
    alphabet.new_render("N", 0, dim_color(c_blue,b))
    alphabet.new_render("T", 6, dim_color(c_blue,b))
    alphabet.new_render("P", 12, dim_color(c_blue,b))
    alphabet.new_render("O", 20, dim_color(c_green,b))
    alphabet.new_render("k", 26, dim_color(c_green,b))
    show()
    
def show_no_ntp():
    ''' Writes "NO NTP" to the display.'''
    clear()
    alphabet.new_render("N", 0, dim_color(c_red,b))
    alphabet.new_render("O", 6, dim_color(c_red,b))
    alphabet.new_render("N", 14, dim_color(c_blue,b))
    alphabet.new_render("T", 20, dim_color(c_blue,b))
    alphabet.new_render("P", 26, dim_color(c_blue,b))
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
                fill_pattern(seg, dim_color(color,b))
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
    for seg in square_1: fill_pattern(seg, dim_color(c_blue,b))
    if indx > 0:
        ii = indx % 14
        np[ii*16 + 19] = dim_color(colon_color, b)
        np[ii*16 + 20] = dim_color(colon_color, b)
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

def shift_horizontally(direction=1, shift_amount=16):
    '''Shifts pixels horizontally, moving them over one spot to the right. 16 is default because that would move the pixel up 8 rows and then down the 8 in the next column putting the pixel right next to where it started'''
    # Create a temporary list to store the shifted colors
    shifted_pixels = [(0,0,0)] * N

    # Shift the colors by the specified amount to the left
    for i in range(N):
        if(i-shift_amount*direction<N): shifted_pixels[i] = np[i - shift_amount* direction]
    
    # Update NeoPixels with the shifted colors
    for i in range(N):
        np[i] = shifted_pixels[i]
        
def shift_left():
    '''Shifts pixels horizontally left, moving them over one spot to the left. '''
    # Create a temporary list to store the shifted colors
    shifted_pixels = [(0,0,0)] * N
    i = 0
    shift = 15
    while(i < N):
        if i + shift < N: shifted_pixels[i] = np[i + shift]
        shift -= 2
        if shift <1: shift = 15
        i += 1
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

def set_global_brightness(brightness):
    global b
    b = brightness
    
# Function to scroll text left to right
def scroll_text(text, color=(5, 5, 5), delay=0.4, isLarge = True):
    if isLarge:
        font = '5x7'
        char_width = 6
        row = 0
    else:
        font = '3x5'
        char_width = 4
        row = 1
    for char in text:
        w = 0
        #print(f"Scrolling character: {char}")
        while w < char_width:
            shift_left()         
            alphabet.render_char(char, PANEL_WIDTH - w, color, font, row)  # draws partial letter
            show()
            time.sleep(delay)
            if(encoder.did_button_press()):
                clear()
                show()
                return
            w += 1
            #print(f"Shift step {w}/{CHAR_WIDTH}")
    i = 0
    while i<PANEL_WIDTH:
        shift_left()
        show()
        time.sleep(delay)
        i+=1
        
scroll_text_string = ""
scroll_color = (5,5,5)
scroll_char_offset = 0
scroll_char_index = 0

def init_infinite_scroll(text, color=(5,5,5)):
    global scroll_color, scroll_text_string
    scroll_text_string = text + "  "
    scroll_color = color
    print(f"init infinite scroll with color: {color} and text: {text}")
    
def infinite_scroll_on_loop():
    global scroll_char_index, scroll_char_offset
    if(scroll_text_string == ""): return
    if scroll_char_index >= len(scroll_text_string): scroll_char_index = 0
    char = scroll_text_string[scroll_char_index]
    shift_left()
    alphabet.new_render(char, PANEL_WIDTH - scroll_char_offset, scroll_color)  # draws partial letter
    show()
    scroll_char_offset +=1
    if(scroll_char_offset>=CHAR_WIDTH):
        scroll_char_offset = 0
        scroll_char_index += 1