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
    for i in range(NPAGES):
        buf = rt.read_eeprom((page0 + i)*PAGE_SIZE, PAGE_SIZE)
        for j in range(RECS_PER_PAGE):
            c, t = struct.unpack_from("LL", buf, j*8)
            tme = time.localtime(t)
            if c > 0: print("%2d-%2d: %6d  %s" % (i, j, c, str(tme)))
            
def list_power():
    list_recs(PAGE_PWR_CYC)
    
def list_time_checks():
    list_recs(PAGE_TIME_CHK)

