# timehelp.py -- Time Functions that help
# dlb, Dec 2023

# These fuctions deal with handling time in the micropython format.
# The 8-tuple format for time is: (year, month, date, hour, minute, second, dow, doy),
# where dow stands for day-of-week, and doy stands for day-of-year.
#
# Note that the 8-tuple does not carry information regarding timezone.
#
# Day-of-year is not used.  However, Day-of-week (dow) is used.  Monday is defined by
# micropython to be zero, so we must stick with that.  

import time

pst_offset = -8 * 3600    # PST -- Pacific Standard Time is used between Nov and Mar
pdt_offset = -7 * 3600    # PDT -- Pacific Daylight Time is used between Mar and Nov

def day_of_week(t):
    ''' Calculates the day-of-week (0=Monday) from a time 8-tuple.'''
    # Note: 1/1/1996 was a Monday.  Monday = 0, Sunday=6.
    tref = (1996, 1, 1, 0, 0, 0, 0, 0)  # Our reference Monday.
    y, mth, day, h, m, s, wd, doy = t
    tchk = (y, mth, day, h, m, s, 0, 0)
    tdif_secs = time.mktime(tchk) - time.mktime(tref)
    ndays = int(tdif_secs / (24*60*60))
    nweeks = int(ndays / 7)
    wday = ndays - (nweeks * 7)
    return int(wday)

def daylight_savings_check(t):
    ''' Returns True if time is in daylight savings. Input time should be local time
    as an 8-tuple.'''
    years, month, date, hour, mins, secs, _, _ = t
    dow = day_of_week(t)
    if month < 3 and month > 11: return False    # Dec, Jan, Feb are Standard Time
    if month > 3 and month < 11: return True     # Apr, May, Jun, July, Aug, Sept, Oct are Daylight Savgins
    # Its only March and November that are special cases
    dx = dow + 1       # Renumber weekdays so that Sunday is zero
    if dx > 6: dx = 0
    date_of_previous_sunday = date - dx
    if month == 3:
        # In March, we are DST if the previous sunday was on or after the 8th.
        if date_of_previous_sunday >= 8:
            if date > date_of_previous_sunday: return True
            # Its the day of change! DST starts at 2 am...
            if hour >= 2: return True
            return False
        return False
    # Its November. Standard time starts on the first Sunday...
    if date_of_previous_sunday < 0: return True
    if date > date_of_previous_sunday: return False
    # Its the day of change! Standard time starts at 2 am...
    if hour < 2: return True
    return False

def apply_offset(t, offset):
    ''' Returns a time with the offset in seconds applied.  Used
    to calculate local time. Input is an 8-tuple, with wday and doy
    ignored. '''
    unix_time = time.mktime(t)
    unix_time += offset
    tt = time.localtime(unix_time)
    return tt

def h24_to_h12(hours):
    ''' Converts 24 hour format into 12 hour format. '''
    h = hours
    if h > 12: h -= 12
    if h == 0: h = 12
    return h

def h12_to_h24(hours, pm):
    ''' Converts 12 hour format into 24 hour format.'''
    if pm:
        if hours >= 12: h = 12
        else: h = hours + 12
    else:
        h = hours
        if h == 12: h = 0
    return h