# alphabet.py -- Renters a characters in the alphyabet into the neopixel array
# dlb, Dec 2023

import neo
import time

# The following is a 5x7 font in an ascii layout, starting with ordinal 32 (space) through ordinal 127 resulting in
# 96 glyphs. Each 5-byte integer encodes one glyph. Each byte in the integer represents one 7 bit column, from 
# top to bottom, and the most significate byte is on the left.  x

font_5x7 = (
     0x0000000000, 0x00007d0000, 0x0070700000, 0x147f147f14, 0x122a7f2a24, 0x6264081323, 0x3649552205, 0x0000600000,        
     0x001c224100, 0x0041221c00, 0x14083e0814, 0x08083e0808, 0x0005060000, 0x0808080808, 0x0003030000, 0x0204081020,        
     0x3e4141413e, 0x00217f0100, 0x2143454931, 0x2241494936, 0x0c14247f04, 0x725151514e, 0x1e29494906, 0x6047485060,        
     0x3649494936, 0x3049494a3c, 0x0036360000, 0x0035360000, 0x0814224100, 0x1414141414, 0x0041221408, 0x2040454830,        
     0x26494f413e, 0x3f4444443f, 0x7f49494936, 0x3e41414122, 0x7f4141413e, 0x7f49494941, 0x7f48484840, 0x3e4141492e,        
     0x7f0808087f, 0x00417f4100, 0x0201417e40, 0x7f08142241, 0x7f01010101, 0x7f2018207f, 0x7f1008047f, 0x3e4141413e,        
     0x7f48484830, 0x3e4145423d, 0x7f484c4a31, 0x3049494906, 0x40407f4040, 0x7e0101017e, 0x7c0201027c, 0x7e010e017e,        
     0x6314081463, 0x7008070870, 0x4345495161, 0x007f414100, 0x2010080402, 0x0041417f00, 0x1020402010, 0x0101010101,        
     0x0040201000, 0x021515150f, 0x7f0911110e, 0x0e11111102, 0x0e1111097f, 0x0e1515150c, 0x083f484020, 0x081515151e,        
     0x7f0810100f, 0x00095f0100, 0x000201115e, 0x7f040a1100, 0x00417f0100, 0x1f100f100f, 0x1f0810100f, 0x0e1111110e,        
     0x1f14141408, 0x0814140c1f, 0x1f08101008, 0x0915151502, 0x107e110102, 0x1e0101021f, 0x1c0201021c, 0x1e0106011e,        
     0x110a040a11, 0x180505051e, 0x1113151911, 0x0008364100, 0x00007f0000, 0x0041360800, 0x0408080408, 0x003c3c3c00)

font_3x5 = (
        0x000000, 0x001700, 0x030003, 0x1F0A1F, 0x121F09, 0x090412, 0x0A151D, 0x000300,
        0x0e1100, 0x110e00, 0x150e15, 0x040e04, 0x100800, 0x040404, 0x001000, 0x180403,
        0x1F111F, 0x021F00, 0x191512, 0x11150A, 0x07041F, 0x171509, 0x0E1509, 0x011D03,
        0x0A150A, 0x12150E, 0x000A00, 0x100A00, 0x040A11, 0x0A0A0A, 0x110A04, 0x011502,
        0x0E1516, 0x1E051E, 0x1F150A, 0x0E110A, 0x1f110E, 0x1f1515, 0x1f0505, 0x0E1119,
        0x1F041F, 0x001F00, 0x08100F, 0x1F041B, 0x1F1010, 0x1F021F, 0x1F011E, 0x0E110E,
        0x1F0502, 0x0E111E, 0x1F051A, 0x121509, 0x011F01, 0x1F101F, 0x0F180F, 0x1F081F,
        0x1B041B, 0x071C07, 0x191513, 0x1f1100, 0x030418, 0x111f00, 0x020102, 0x101010,
        0x010200, 0x1E051E, 0x1F150A, 0x0E110A, 0x1f110E, 0x1f1515, 0x1f0505, 0x0E1119,
        0x1F041F, 0x001F00, 0x08100F, 0x1F041B, 0x1F1010, 0x1F021F, 0x1F011E, 0x0E110E,
        0x1F0502, 0x0E111E, 0x1F051A, 0x121509, 0x011F01, 0x1F101F, 0x0F180F, 0x1F081F,
        0x1B041B, 0x071C07, 0x191513, 0x041F11, 0x001B00, 0x111f04, 0x010201 )

# Following is a 7x5 font rendered in an 8x5 format
x_0 = (0,0,1,1,1,1,1,0, 0,1,0,0,0,0,0,1, 0,1,0,0,0,0,0,1, 0,1,0,0,0,0,0,1, 0,0,1,1,1,1,1,0 )
x_1 = (0,0,0,0,0,0,0,0, 0,1,0,0,0,0,0,1, 0,1,1,1,1,1,1,1, 0,0,0,0,0,0,0,1, 0,0,0,0,0,0,0,0 )
x_2 = (0,0,1,0,0,1,1,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,0,1,1,0,0,0,1 )
x_3 = (0,0,1,0,0,0,1,0, 0,1,0,0,0,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,0,1,1,0,1,1,0 )
x_4 = (0,1,1,1,1,0,0,0, 0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0, 0,1,1,1,1,1,1,1, 0,0,0,0,1,0,0,0 )
x_5 = (0,1,1,1,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,0,1,1,0 )
x_6 = (0,0,1,1,1,1,1,0, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,0,1,1,0 )
x_7 = (0,1,0,0,0,0,0,0, 0,1,0,0,0,1,1,1, 0,1,0,0,1,0,0,0, 0,1,0,0,1,0,0,0, 0,1,1,1,0,0,0,0 )
x_8 = (0,0,1,1,0,1,1,0, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,0,1,1,0,1,1,0 )
x_9 = (0,0,1,1,0,0,1,0, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,1,0,0,1,0,0,1, 0,0,1,1,1,1,1,0 )
x_colon = (0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,1,0,1,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0 )
x_plus  = (0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0, 0,0,1,1,1,1,1,0, 0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0 )
x_minus = (0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0 )
x_equal = (0,0,0,0,1,0,1,0, 0,0,0,0,1,0,1,0, 0,0,0,0,1,0,1,0, 0,0,0,0,1,0,1,0, 0,0,0,0,1,0,1,0 )
x_a     = (0,0,0,0,0,0,1,0, 0,0,0,1,0,1,0,1, 0,0,0,1,0,1,0,1, 0,0,0,1,0,1,0,1, 0,0,0,0,1,1,1,1 )
x_b     = (0,1,1,1,1,1,1,1, 0,0,0,0,1,0,0,1, 0,0,0,1,0,0,0,1, 0,0,0,1,0,0,0,1, 0,0,0,0,1,1,1,0 )
x_f     = (0,0,0,0,1,0,0,0, 0,0,1,1,1,1,1,1, 0,1,0,0,1,0,0,0, 0,1,0,0,0,0,0,0, 0,0,1,0,0,0,0,0 )
x_i     = (0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,1,0,1,1,1, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0 )  # reduced.
x_k     = (0,1,1,1,1,1,1,1, 0,0,0,0,0,1,0,0, 0,0,0,0,1,0,1,0, 0,0,0,1,0,0,0,1, 0,0,0,0,0,0,0,0 )
x_o     = (0,0,0,0,1,1,1,0, 0,0,0,1,0,0,0,1, 0,0,0,1,0,0,0,1, 0,0,0,1,0,0,0,1, 0,0,0,0,1,1,1,0 )
x_w     = (0,0,0,1,1,1,1,1, 0,0,0,0,0,0,0,1, 0,0,0,1,1,1,1,1, 0,0,0,0,0,0,0,1, 0,0,0,1,1,1,1,1 )
x_N     = (0,1,1,1,1,1,1,1, 0,0,0,1,0,0,0,0, 0,0,0,0,1,0,0,0, 0,0,0,0,0,1,0,0, 0,1,1,1,1,1,1,1 )
x_O     = (0,0,1,1,1,1,1,0, 0,1,0,0,0,0,0,1, 0,1,0,0,0,0,0,1, 0,1,0,0,0,0,0,1, 0,0,1,1,1,1,1,0 )

chars = "0123456789:+-=abfikowNO"
font = (x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8, x_9,
        x_colon, x_plus, x_minus, x_equal,
        x_a, x_b, x_f, x_i, x_k, x_o, x_w, x_N, x_O)

NPixels = 256  # Hack.  Should be a globle constan

def get_index(c):
    ic = 0
    while ic < len(chars):
        if c == chars[ic]: return ic
        ic += 1
    return -1

def render(pixels, column0, color, c):
    '''Renders a character in the neopixel array starting at column0, using
    the given color.'''
    ic = get_index(c)
    if ic < 0: return
    bitmap = font[ic]
    for icolumn in range(5):
        for irow in range(8):
            indx = icolumn * 8 + irow
            if bitmap[indx] != 0:
                irealcol = column0 + icolumn
                if irealcol % 2 == 0: j = irealcol * 8 + irow
                else:                 j = irealcol * 8 + (7 - irow)
                if j >=0 and j < NPixels: pixels[j] = color
 
def new_render(c, column, color):
    io = ord(c) - 32
    if io < 0 or io >= 96: return
    glyph = font_5x7[io]
    for icol in range(5):
        b = (glyph >> ((4 - icol) * 8)) & 0x00FF
        for irow in range(7):
            if (b & 0x01) != 0: neo.set_color(icol + column, irow, color)
            b = (b >> 1) & 0x07F

def render_char(c, column, color, size='5x7', r=0):
    if size == '5x7':
        font = font_5x7
        font_width = 5
        font_height = 7
    elif size == '3x5':
        font = font_3x5
        font_width = 3
        font_height = 5
    else:
        raise ValueError("Unsupported font size")
    
    io = ord(c) - 32
    if io < 0 or io >= len(font):
        return
    
    glyph = font[io]
    for icol in range(font_width):
        b = (glyph >> (font_width - 1 - icol) * 8) & 0x00FF  
        for irow in range(font_height):
            if (b & 0x01) != 0:
                display_row = irow+r
                if size =='3x5': display_row = font_height-1 - irow +r
                neo.set_color(icol + column, display_row, color)
            if size == '5x7':
                b = (b >> 1) & 0x07F
            elif size == '3x5':
                b = (b >> 1) & 0x05F

def show_char(c, column, color, size ='5x7'):
    neo.solid(neo.c_black)
    render_char(c, column, color, size)
    neo.show()

def show_test():
    line = ''' ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,"'?!@_*#$%&()+-/:;<=>[\]^`{|}~'''
    for c in line:
        show_char(c,0,(15,0,55))
        time.sleep(0.65)
        
def short_test(font = '5x7'):
    line = ''' ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,"'?!@_*#$%&()+-/:;<=>[\]^`{|}~'''
    for c in line:
        neo.solid(neo.c_black)
        render_char(c,0, (22,22,0), font)
        neo.show()
        time.sleep(.35)

    

def hello_world(font = '3x5'):
    if font == '5x7':
        font_width = 5
    elif font == '3x5':
        font_width = 3
        
    neo.solid(neo.c_black)
    render_char('H',0, (22,22,0), font)
    render_char('e',font_width, (22,0,22), font)
    render_char('l',font_width*2, (0,22,22), font)
    render_char('l',font_width*3, (0,0,22), font)
    render_char('o',font_width*4, (22,0,0), font)
    neo.show()




