# main.py -- Main clock logic
# dlb, Dec 2023

# Implementer's notes:
#
# Python time on the Pico W, under the micropython enviroment is kept
# by using the machine.RTC module.  It is unclear if this module is
# using the RP2040 chip's built-in RTC hardware.  However, it doesn't
# really matter since this code doesn't depend on the RP2040's notion
# of time.  But it is interesting to note that upon USB connection with
# Thorny the machine.RTC module is synced to the time of the host (i.e., Windows)
#
# The PICO W is connected to a RTC backup module that keeps time as well
# as the RP2040 hardware.  The backup system is based on a DS3231 chip, with
# a CR2023 battery that should last years.  Once set, this system should
# keep time for a few years without AC external power.  The DS3231 is
# advertised to be accurate to plus or minus 2 minutes per year.
#
# This device also has a wifi module.  If the module can connect to the
# interrnet, NTP time can be obtained, in which case the time should be accurate
# to within one second.
#
# Therefore, the inital time (and updated time) can come from three sources:
# the RTC backup, NTP, or manually via interaction with the code using Thorny.
#
# Time Algorithem
# For display output, the DS3231 time value is used. If the year in the DS3231 is
# less than 2010, then we assume that the DS3231 does not know the time -- and an
# error condition is shown on the display.  Time updates (synchronizations) are
# attemped at startup if the time is found to be invalid, and once every night at
# about 2 am.  If a valid NTP time is obtained, then the DS3132 is updated to
# match NTP time.  The time that the DS3231 is updated is recorded in EEPROM.
#
# Stale Time
# If the clock runs for more than about a month without being updated and/or checked by
# wifi/NTP, then the time is decleared to be stale.  A stale time is indicated by blue
# colon between the hour and minute digits.  Normally the colon is red.
#
# Time Zone and Daylight Savings
# This clock is programmed to show the pacific time zone.  It is also programmed
# to automatically switch between daylight savings and standard time.  The algorithem
# for switching depends on past and current government policy, so the code might need
# if the rules regarding daylight savings changes.
#
# Wifi Access
# This code is hardwired to check for a list of wifi access points to gain connection to
# the internet.  Currently this list includes the Brandon's house, and the school's Robotic
# rooms.
#
# Critical Times
# One feature of this clock is that it can change the color of the clock digits at different
# times of day, for different days of the week.  We call these critical times.  Currently the
# critical times are from 8:50pm till 9:05 on Monday through Thursday -- since these are the
# times the robot team needs to cleanup and leave the lab.  There is also a crital time near
# 3am, since this is the time the builting alarm automatically arms itself.
#
# History
# A record is kept for each power up cycle, and each time the RTC is updated with NTP Time.
# There are 64 records for each activity, on a rollover buffer in EEPROM.  This data can
# be accessed manually by interacting with the code using Thorny.
#

import machine
from machine import RTC
from machine import Timer
import history as hist
import neo
import ntptime as ntp
import rtcmod as rtc
import timehelp as th
import timesync as sync
import time

Version = "V0.9, 12/10/23"
ClockId = "dev_unit"

critical_times = [
    ((20, 50), (21, 05), (0, 1, 2, 3), neo.c_red, neo.c_white, 10),  
    ((02, 55), (03, 01), (0, 1, 2, 3, 4, 5, 6), neo.c_red, neo.c_white, 8)]

requested_render = (-1, -1, neo.c_red, neo.c_white, neo.c_blue, 0)
last_render = (-100, -100, neo.c_black, neo.c_black)
blink_counter = 0
blink_even = False
time_valid = False

def update_display(timer):
    global requested_render, last_render, blink_even, blink_counter
    h, m, dc, dac, cc, blink_period = requested_render
    if blink_period > 0:
        blink_counter += 1
        if blink_counter > blink_period: blink_counter = 0
        if blink_counter >= blink_period / 2: dc = dac
    new_render = (h, m, dc, cc)
    if new_render != last_render:
        neo.solid(neo.c_black)
        neo.render_time(h, m, dc, cc)
        neo.show()
        last_render = new_render
        
def critical_time_check(t):
    " Returns params for critical times, if active."
    wd = th.day_of_week(t)
    tchk = t[3] + (t[4] / 60.0)
    for ct in critical_times:
        t1, t2, wds, c1, c2, bp = ct
        tc1 = t1[0] + t1[1] / 60.0
        tc2 = t2[0] + t2[1] / 60.0
        if wd in wds:
            if tchk >= tc1 and tchk <= tc2:
                return (c1, c2, bp)
    return (neo.c_red, neo.c_red, 0)

def wait_for_network_time(must_connect = False):
    '''Used at startup. Disables clock since no time to display.  Trys to
    connect to wifi.'''
    global time_valid
    icount = 0
    while True:
        neo.blue_square(0)
        print("Scanning for wifi...")
        ntp.init()
        tstart = time.time()
        while True:
            access_point = ntp.scan()
            if access_point is not None: break
            icount += 1
            neo.blue_square(icount, (40, 0, 40))
            time.sleep(0.5)
            if time.time() - tstart > 30:
                neo.show_no_wifi()
                time.sleep(5.0)
                tstart = time.time()
                neo.blue_square(0)
        ssid, bssid, chan, signal, _, _, pw = access_point
        print("Found wifi access point. Name=%s, Chan=%d, signal=%d, pw=%s" % (ssid, chan, signal, pw))
        neo.blue_square(icount, neo.c_blue)
        print("Connecting to wifi...")
        ntp.start_connect(ssid, pw)
        tstart = time.time()
        while True:
            if ntp.is_connected(): break
            icount += 1
            neo.blue_square(icount, neo.c_blue)
            time.sleep(0.5)
            if time.time() - tstart > 30.0: break
        if not ntp.is_connected():
            print("Unable to connect...")
            ntp.network_off()
            neo.show_no_wifi()
            time.sleep(6.0)
            if not must_connect: return
            neo.blue_square(0)
            continue
        neo.show_wifi_ok()
        time.sleep(4.0)
        neo.blue_square(icount, neo.c_green)
        ntp.print_network_info()
        neo.blue_square(icount, neo.c_green)
        print("Using NTP to get time...")
        tstart = time.time()
        t = None
        while True:
            t = ntp.ntp()
            if t is not None: break
            icount += 1
            neo.blue_square(icount, neo.c_green)
            time.sleep(0.5)
            if time.time() - tstart > 10.0: break    
        if t is None:
            print("Unable to get NTP time.")
            ntp.network_off()
            neo.show_no_ntp()
            time.sleep(6.0)
            if not must_connect: return
            continue
        neo.show_ntp_ok()
        time.sleep(4.0)
        str_tme = str(time.localtime(t))
        print("NTP Time Recevied.")
        print("Setting RTC Module to UTC Time: %s" % str_tme)
        rtc.set_time(time.localtime(t))
        hist.time_check(t)
        ntp.network_off()
        time_valid = True
        return
            
def startup():
    global time_valid, requested_render
    print("Clock Startup. Id=%s   Version=%s" % (ClockId, Version))
    print("Running startup anaimation...")
    neo.startup_animation()
    print("Initializing eeprom...")
    hist.init_eeprom()
    tuse = rtc.get_time()
    year, month, date, hours, mins, seconds, dow, doy = tuse
    print("Time found from rtc at startup = ", tuse)
    tuse = time.mktime(tuse)
    if year < 2010:
        time_valid = False  # We don't have a valid time.
        tuse = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0))
        print("RTC time is invaid.")
    else:
        time_valid = True
    hist.power_cycle_increment(tuse)
    wait_for_network_time(must_connect = not time_valid)

def run():
    global time_valid, requested_render
    startup()
    t1 = Timer(period=50, mode=Timer.PERIODIC, callback=update_display)
    last_dst = True  
    dst_lockout = False
    while True:
        t = rtc.get_time()   # This SHOULD be UTC time.
        tutc = time.mktime(t)
        years = t[0]
        if years < 2010: valid_time = False
        else:            valid_time = True
        if not valid_time:
            requested_render = (-1, -1, neo.c_red, neo.c_red, neo.c_white, 0)
            time.sleep(1.0)
            continue
        # If it has been a long time since a time sync, turn the colon to blue.
        tlast_update = hist.get_last_time_check()
        if tlast_update is None:
            colon_color = neo.c_blue
        else:
            tspan = tutc - tlast_update
            if tspan > 30 * 24 * 3600:
                # Longer than 30 days!
                colon_color = neo.c_blue
            else: colon_color = neo.c_red
        # Use last PST/PDT setting to determin if daylight savings is in effect
        if last_dst: tlocal = th.apply_offset(t, th.pdt_offset)
        else:        tlocal = th.apply_offset(t, th.pst_offset)
        if not dst_lockout:
            new_dst = th.daylight_savings_check(tlocal)
            if new_dst != last_dst:
                if new_dst: print("Daylight Savings is changing to ON.")
                else:       print("Daylight Savings is changing to OFF.")
                last_dst = new_dst
                if last_dst: tlocal = th.apply_offset(t, th.pdt_offset)
                else:        tlocal = th.apply_offset(t, th.pst_offset)
                dst_lockout = True
        else:
            h = tlocal[3]
            if h > 8: dst_lockout = False      
        dc1, dc2, blink_period = critical_time_check(tlocal)
        h, m = tlocal[3], tlocal[4]
        h = th.h24_to_h12(h)
        requested_render = (h, m, dc1, dc2, colon_color, blink_period)
        time.sleep(0.5)
        sync.sync_time(tutc)
        
def set_rtc_with_test(test_name):
    ''' Sets the clock to some special times for testing. '''
    if test_name == "crit":
        rtc.set_time((2024, 2, 6, 04, 49, 55, 1, 0))
    if test_name == "crit2":
        rtc.set_time((2024, 2, 6, 05, 04, 55, 1, 0))
    if test_name == "dst0":
        rtc.set_time((2024, 3, 8, 06, 50, 0, 1, 0))
    if test_name == "dst1":
        rtc.set_time((2024, 3, 10, 09, 59, 55, 1, 0))
    if test_name == "pst":
        rtc.set_time((2024, 11, 3, 08, 59, 55, 1, 0))
    run()
    
def set_and_go():
    ''' Use NTP to set the rtc.  Assumes no connection.'''
    ntp.init()
    ap = ntp.scan()
    if ap is None:
        print("No access point found. Abort.")
        return
    ssid, bssid, chan, signal, _, _, pw = ap
    print("Found AP.  Name=%s, Chan=%d, Signal=%d, PW=%s" % (ssid, chan, signal, pw))
    ntp.connect(ssid, pw)
    t_utc = ntp.ntp()
    if t_utc is None:
        print("Unable to get NTP time.  Abort.")
        return
    t_tuple = time.localtime(t_utc)
    print("Setting UTC Time to = %s" % (str(t_tuple)))
    rtc.set_time(t_tuple)
    hist.time_check(t_utc)
    run()
