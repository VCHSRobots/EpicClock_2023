#rtcmod.py -- Provides a driver for the battery backed Real-Time-Clock module
#dlb, Dec 2023

# Note, the RTC module includes a DS3231 chip located at address 104 (0x68)
# and a 32K bit EEROM chip (AT24C32) located at address 87 (0x57)

# The AT24C32 has 4K bytes!  The addresses then wrap as modulo 4096.
#
# More important info about the AT24C32.  You must be careful to only
# read and write around the page boundaries.  A page is 32 bytes long,
# and there are 128 pages in the memory.  For best resultes a read or
# write should start on a page boundry, and be limited to 32 bytes.

from machine import Pin, I2C, SoftI2C
import timehelp as th
import time

i2c = SoftI2C(Pin(5), Pin(4), freq=100_000)         # Software I2C
#i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq= 100_000)  # Hardware I2C
rtc_adr    = 0x68
eeprom_adr = 0x57

last_write_time = None
delay_start = None

def start_eeprom_delay():
    ''' Mark a start time to delay further operations while waiting for
    a write to finish.'''
    global last_write_time, delay_start
    last_write_time = time.time()
    delay_start = time.ticks_ms()

def eeprom_delay():
    ''' Wait here for at least 10ms to allow previous writes to finish.'''
    global last_write_time, delay_start
    if delay_start is None: return
    if last_write_time is None: return
    dsecs = time.time() - last_write_time
    if dsecs > 2: return
    while True:
        dly = time.ticks_diff(time.ticks_ms(), delay_start) 
        if dly > 10: return
    delay_start = None
    
def write_eeprom(addr, data):
    ''' Writes bytes of data to the eeprom at the given address. Be
    careful to obey page boundary and 32 byte rules.'''
    eeprom_delay()
    n = len(data)
    outdata = bytearray(n + 2)
    outdata[0]=addr >> 8   #MSB
    outdata[1]=addr & 0xFF #LSB
    for i in range(n): outdata[i + 2] = data[i]
    i2c.writeto(eeprom_adr, outdata)
    # Specs say a write might take 5 ms (per byte?) before the eeprom will
    # respond to another request
    start_eeprom_delay()

def read_eeprom(addr, nbytes):
    ''' Reads bytes of data from the eeprom at the given address'''
    eeprom_delay()
    addr_buf = bytearray(2)
    addr_buf[0] = addr >> 8   #MSB
    addr_buf[1] = addr & 0xFF #LSB
    i2c.writeto(eeprom_adr, addr_buf)
    x = i2c.readfrom(eeprom_adr, nbytes)
    return x
    
def dump_eeprom(a0, n):
    dump = ""
    nrows = int((n / 64) + 1)
    for i in range(nrows):
        a = i * 64 + a0
        ss = "%04d: " % a
        for j in range(2):
            x = read_eeprom(a + j * 32, 32)
            sx = ""
            for ii in range(32):
                if x[ii] >= 32 and x[ii] < 127: sx += chr(x[ii])
                elif x[ii] != 0: sx += '-'
                else: sx += '.'
            ss += sx
        print(ss)
        dump +=ss + "\n"
    return dump
        
        
def get_time():
    ''' Returns time as a 8-tuple: year, month, day, hour, min, sec, wday, doy.
    Uses 24 hour format.  Should be UTC time!  wday and doy should be ignored.'''
    raw = i2c.readfrom_mem(rtc_adr, 0, 7)
    secs = (((raw[0] >> 4) & 0x0F) * 10) + (raw[0] & 0x0F)
    mins = (((raw[1] >> 4) & 0x0F) * 10) + (raw[1] & 0x0F)
    is12 = ((raw[2] & 0x40) != 0)
    if is12:
        hours_12 = (((raw[2] >> 4) & 0x01) * 10) + (raw[2] & 0x0F)
        ispm = ((raw[2] & 0x020) != 0)
        if ispm:
            if hours_12 < 12: hours_24 = hours_12 + 12
            else: hours_24 = hours_12
        else:
            if hours_12 >= 12: hours_24 = 0
            else: hours_24 = hours_12
    else:
        hours_24 = (((raw[2] >> 4) & 0x03) * 10) + (raw[2] & 0x0F)
    wday  = raw[3] & 0x07
    date  = (((raw[4] >> 4) & 0x03) * 10) + (raw[4] & 0x0F)
    month = (((raw[5] >> 4) & 0x01) * 10) + (raw[5] & 0x0F)
    year  = (((raw[6] >> 4) & 0x0F) * 10) + (raw[6] & 0x0F) + 2000
    return (year, month, date, hours_24, mins, secs, wday, 0)

def bcd(x):
    ''' Returns the value x (0-255) in Binary coded decimal format. '''
    x10s = int(x / 10)
    x1s  = x - (x10s * 10)
    v = ((x10s << 4) & 0x0F0) | (x1s & 0x0F)
    return v

def set_time(t):
    ''' Sets time in RTC from a 8-tuple: year, month, date, hour, min, sec, dow, doy.
    Uses 24 hour format.  Time should be given in UTC!  dow and doy ignored.'''
    year, month, date, hours, mins, secs, wday, doy = t
    dow = th.day_of_week(t)
    data = bytearray(7)
    data[0] = bcd(secs)
    data[1] = bcd(mins)
    data[2] = bcd(hours)
    data[3] = bcd(dow)
    data[4] = bcd(date)
    data[5] = bcd(month)
    data[6] = bcd(year - 2000)
    i2c.writeto_mem(rtc_adr, 0, data)
    


    
    
    
    
    
    