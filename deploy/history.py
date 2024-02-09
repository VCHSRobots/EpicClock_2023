# history.py -- Maintains clock history in eeprom
# dlb, Dec 2023

# Here we use EEPROM to record when the clock
# was reset to a known time.  Also records the number
# of main power cycles that occurr.

# This is done as a list of records.  Each record is
# 8 bytes, 4 bytes for a count, and 4 bytes for a
# unix time value (in UTC).

# Because of the way that the eeprom works, we want
# to make our records fit an eeprom "page" which is 32
# bytes.  So, we choose 64 records in the database,
# where 4 records fit in a page, so 16 pages are used
# for each history catalog: one for power ups, and one
# for clock checks.

import struct
import rtcmod as rt
import time

PAGE_SIZE     = 32
REC_SIZE      =  8 
RECS_PER_PAGE = int(PAGE_SIZE / REC_SIZE)   # This must be an interger
NPAGES        = 16
NRECS         = NPAGES * RECS_PER_PAGE  # Total number of records before rollover
PAGE_CLK_ID   =  1                      # Page for Clock ID
PAGE_PWR_CYC  =  2                      # First Page for Power cycle records
PAGE_TIME_CHK = 20                      # First Page for Time Check records
PAGE_BRIGHT   = 37						# Page for saving brightness level and render state
PAGE_COLORS   = 38
PAGE_WIFI_SSID	  = 41						
PAGE_WIFI_PW	  = 42						


def wipe_eeprom(clock_id = b'default'):
    ''' Completely clears the eeprom, and then writes our signature.'''
    buf = bytearray(32)
    for i in range(128):
        rt.write_eeprom(i*32, buf)
    rt.write_eeprom(0, b'epicclock')
    write_clock_id(clock_id)
    
def init_eeprom():
    ''' Checks to see if the eeprom has been initized. If not
    write a signature and prepares empty records.'''
    buf = rt.read_eeprom(0, 9)
    if buf == b'epicclock': return
    wipe_eeprom()

def write_clock_id(clock_id):
    ''' Writes the clock id into eeprom. (Can be str or bytes).'''
    if type(clock_id) is str: clock_id = bytes(clock_id, 'ascii') 
    clock_id += 16 * b'\00'
    clock_id = clock_id[0:16]
    rt.write_eeprom(PAGE_CLK_ID*PAGE_SIZE, clock_id)
    
def read_clock_id():
    ''' Returns the clock id as a string.'''
    bb = rt.read_eeprom(PAGE_CLK_ID*PAGE_SIZE, 16)
    s = ""
    for b in bb:
        if b == 0: return s
        s += chr(b)
    return s

def write_render_style(render_style):
    rt.write_eeprom(PAGE_BRIGHT * PAGE_SIZE + 3, [render_style])
    
def read_render_style():
    return rt.read_eeprom(PAGE_BRIGHT*PAGE_SIZE+3, 1)[0]
    
def write_brightness(brightness):
    ''' Writes the brightness into eeprom as 2 bytes'''
    intBrightness = int (brightness*1000.0)
    b1 = intBrightness & 0x0ff
    b2 = intBrightness >> 8 & 0x0ff
    b = bytearray([b1,b2])
    rt.write_eeprom(PAGE_BRIGHT*PAGE_SIZE, b)
    
def read_brightness():
    ''' reads the brightness into eeprom as 2 bytes'''
    bb = rt.read_eeprom(PAGE_BRIGHT*PAGE_SIZE, 2)
    intBrightness = (bb[1] <<8) | bb[0]
    brightness = intBrightness/1000.0
    if brightness <.0001: brightness = .03
    return brightness

def write_colors(digit_color, digit_state, colon_color, colon_state, seconds_color, seconds_state, am_color, am_state):
    ''' Writes the digit color and state into eeprom as 4 bytes'''
    dr, dg, db = digit_color
    cr, cg, cb = colon_color
    sr, sg, sb = seconds_color
    ar, ag, ab = am_color
    
    b = bytearray([dr, dg, db, digit_state, cr, cg, cb, colon_state, sr, sg, sb, seconds_state, ar, ag, ab, am_state])
    rt.write_eeprom(PAGE_COLORS * PAGE_SIZE, b)
    
def read_colors():
    '''reads the colors and their transitional states'''
    dr, dg, db, digit_state, cr, cg, cb, colon_state, sr, sg, sb, seconds_state, ar, ag, ab, am_state = rt.read_eeprom(PAGE_COLORS * PAGE_SIZE, 16)
    
    #if all zeros then initilize to this color
    if dr == dg == db == cr == cg == cb == sr == sg == sb == ar == ag == ab == 0:
        dr = 255
        db = 40
        cr = 255
        cb = 40
        sg = 255
        sb = 40
        ag = 255
        ab = 40
        
    digit_color   = (dr, dg, db)
    colon_color   = (cr, cg, cb)
    seconds_color = (sr, sg, sb)
    am_color      = (ar, ag, ab)
    
    return digit_color, digit_state, colon_color, colon_state, seconds_color, seconds_state, am_color, am_state

def write_wifi(ssid, pw):
    ''' Writes WiFi SSID and password into EEPROM.'''
    empty_bytes = bytes([0] * PAGE_SIZE)
    if type(ssid) is str:
        ssid = bytes(ssid, 'utf-8')[:PAGE_SIZE]
    else:
        ssid = ssid[:PAGE_SIZE]

    if type(pw) is str:
        pw = bytes(pw, 'utf-8')[:PAGE_SIZE]
    else:
        pw = pw[:PAGE_SIZE]
    
    rt.write_eeprom(PAGE_WIFI_SSID * PAGE_SIZE, empty_bytes)
    rt.write_eeprom(PAGE_WIFI_PW * PAGE_SIZE, empty_bytes)
    
    rt.write_eeprom(PAGE_WIFI_SSID * PAGE_SIZE, ssid)
    rt.write_eeprom(PAGE_WIFI_PW * PAGE_SIZE, pw)

def read_wifi():
    ''' Reads WiFi SSID and password from EEPROM.'''
    wifi_data = rt.read_eeprom(PAGE_WIFI_SSID * PAGE_SIZE, PAGE_SIZE*2)
    
    ssid_bytes = wifi_data[:PAGE_SIZE]
    pw_bytes = wifi_data[PAGE_SIZE:]
    print("ssid_bytes:", ssid_bytes)
    print("pw_bytes", pw_bytes)
    try:
        ssid = ssid_bytes.decode('utf-8').split('\x00', 1)[0]
        pw = pw_bytes.decode('utf-8').split('\x00', 1)[0]
    except Exception as e:
        print("could not decode wifi. Exception: \r\n", e)
        return "", ""
    

    return ssid, pw

def get_last(page0):
    ''' Returns the last best record as a 4-tuple or None.
    The 4-tuple is (page_num, index, count, unix-time)'''
    ibest = (0, 0, 0, 0)
    for i in range(NPAGES):
        buf = rt.read_eeprom((page0 + i)*PAGE_SIZE, PAGE_SIZE)
        for j in range(RECS_PER_PAGE):
            c, t = struct.unpack_from("LL", buf, j*8)
            if c > 0:
                if c > ibest[2]: ibest = (i, j, c ,t)
    return ibest

def write_record(ipage, index, buf):
    ''' Write one record into the eeprom at the given page and index.'''
    rt.write_eeprom(ipage * PAGE_SIZE + index * REC_SIZE, buf)

def power_cycle_increment(t):
    ''' Increment the power cycle count and store the time in the history.'''
    ipage, indx, count, tt = get_last(PAGE_PWR_CYC)
    count += 1
    indx += 1
    if indx >= RECS_PER_PAGE:
        indx = 0
        ipage += 1
        if ipage >= NPAGES: ipage = 0
    buf = struct.pack("LL", count, t)
    write_record(ipage + PAGE_PWR_CYC, indx, buf)
    
def time_check(t):
    ''' Store the time that the time was checked with ntp, or manually.'''
    ipage, indx, count, tt = get_last(PAGE_TIME_CHK)
    count += 1
    indx += 1
    if indx >= RECS_PER_PAGE:
        indx = 0
        ipage += 1
        if ipage >= NPAGES: ipage = 0
    buf = struct.pack("LL", count, t)
    write_record(ipage + PAGE_TIME_CHK, indx, buf)
    
def get_last_time_check():
    ''' Returns the UTC time of the last time sync from eeprom. Or None
    if nothing found.'''
    ipage, indx, count, tt = get_last(PAGE_TIME_CHK)
    if count <= 0: return None
    return tt

def get_last_power_cycle():
    ''' Returns the UTC time of the last time the clock was powered up, or
    None if nothing found.'''
    ipage, indx, count, tt = get_last(PAGE_PWR_CYC)
    if count <= 0: return None
    return tt

def list_recs(page0):
    ''' List records found in history, given the starting page number.'''
    result_string = ""
    for i in range(NPAGES):
        buf = rt.read_eeprom((page0 + i)*PAGE_SIZE, PAGE_SIZE)
        for j in range(RECS_PER_PAGE):
            c, t = struct.unpack_from("LL", buf, j*8)
            #print(f"c={c} t={t}")
            tme = time.localtime(t)
            s = "%2d-%2d: %6d  %s\n" % (i, j, c, str(tme))
            #print(s)
            if c > 0: result_string += s
    
    print(f"list_recs {page0}: \n {result_string}")
    return result_string
            
def list_power():
    return list_recs(PAGE_PWR_CYC)
    
def list_time_checks():
    return list_recs(PAGE_TIME_CHK)

