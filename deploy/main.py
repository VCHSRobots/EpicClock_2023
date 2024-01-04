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
import next_color
import encoder

Version = "V0.9, 12/10/23"
ClockId = "dev_unit"


class ClockStates:
    BRIGHTNESS = 1
    DIGIT_COLOR = 2
    COLON_COLOR = 3
    SECONDS_COLOR = 4
    AM_COLOR = 5
    RAINBOW = 6


critical_times = [ ]
# Epic Robots at the School:
#    ((20, 50), (21, 05), (0, 1, 2, 3), neo.c_red, neo.c_white, 10),  
#    ((02, 55), (03, 01), (0, 1, 2, 3, 4, 5, 6), neo.c_red, neo.c_white, 8)]

requested_render = (-1, -1, -1, True, neo.c_white, neo.c_blue, 0)
last_render = (-100, -100,-100, True, neo.c_black, neo.c_black, 0)
blink_counter = 0
blink_even = False
time_valid = False
digit_color = neo.c_teal
digit_color_state = next_color.ColorStates.TO_BLUE
colon_color = neo.c_teal
colon_color_state = next_color.ColorStates.TO_BLUE
seconds_color = neo.c_purple
seconds_color_state = next_color.ColorStates.BACK_TO_RED
am_color = neo.c_teal
am_color_state = next_color.ColorStates.TO_BLUE

COLOR_SPEED = 15
clock_state = ClockStates.BRIGHTNESS
    
    
    
def update_display(timer):
    global requested_render, last_render, blink_even, blink_counter, digit_color, brightness
    h, m, s, isAM, dac, cc, blink_period = requested_render
    if blink_period > 0:
        blink_counter += 1
        if blink_counter > blink_period: blink_counter = 0
        if blink_counter >= blink_period / 2: dc = dac
    new_render = (h, m, s, isAM, digit_color, cc, brightness)
    if new_render != last_render:
        neo.solid(neo.c_black)
        neo.render_time(h, m, s, isAM, digit_color, cc, seconds_color, am_color, brightness)
        draw_menu_light()
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
    return (neo.c_teal, neo.c_teal, 0)

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
            print("No access point found")
            icount += 1
            neo.blue_square(icount, (40, 0, 40))
            time.sleep(0.5)
            if time.time() - tstart > 30:
                neo.show_no_wifi()
                time.sleep(5.0)
                tstart = time.time()
                neo.blue_square(0)
                if not must_connect: return
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
        time.sleep(2.0)
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
        time.sleep(2.0)
        str_tme = str(time.localtime(t))
        print("NTP Time Recevied.")
        print("Setting RTC Module to UTC Time: %s" % str_tme)
        rtc.set_time(time.localtime(t))
        hist.time_check(t)
        ntp.network_off()
        time_valid = True
        return
            
def startup():
    global time_valid
    print("Clock Startup. Id=%s   Version=%s" % (ClockId, Version))
    print("Running rainbow_animation anaimation...")
    #def rainbow_animation(loops=50, dim_amount = .93, initial_brightness=0.1, speed=56):
    neo.rainbow_animation(15, .8, brightness)
    print("Initializing eeprom...")
    hist.init_eeprom()
    tuse = rtc.get_time()
    year, month, date, hours, mins, seconds, dow, doy = tuse
    print("Time found from rtc at startup = ", tuse)
    tuse = time.mktime(tuse)
    if year < 2010:
        time_valid = False  # We don't have a valid time.
        tuse = time.mktime((2000, 1, 1, True, 0, 0, 0, 0, 0))
        print("RTC time is invaid.")
    else:
        time_valid = True
    hist.power_cycle_increment(tuse)
    wait_for_network_time(must_connect = not time_valid)

def is_valid_time(years):
    return years >= 2010

def update_colon_color(tutc, tlast_update):
    global colon_color
    if tutc - tlast_update > 30 * 24 * 3600:
        return (0,0,255)
    return colon_color

def apply_timezone_offset(t, last_dst):
    return th.apply_offset(t, th.pdt_offset) if last_dst else th.apply_offset(t, th.pst_offset)

def handle_dst_change(new_dst, last_dst, t):
    if new_dst != last_dst:
        print(f"Daylight Savings is changing to {'ON' if new_dst else 'OFF'}.")
        return new_dst, apply_timezone_offset(t, th.pdt_offset) if new_dst else apply_timezone_offset(t, th.pst_offset), True
    return last_dst, None, False

def start_timer(timer):
    timer.init(period=50, mode=Timer.PERIODIC, callback=update_display)
    
def stop_timer(timer):
    timer.deinit()
    
def read_history():
    '''reads the history from eeprom and saves it to our global variables'''
    global brightness, digit_color, digit_color_state, colon_color, colon_color_state, seconds_color, seconds_state, am_color, am_color_state

    brightness = hist.read_brightness()

    if brightness <= 0:
        brightness = 0.04
    elif brightness > 1:
        brightness = 1

    digit_color, digit_color_state, colon_color, colon_color_state, seconds_color, seconds_color_state, am_color, am_color_state = hist.read_colors()

    print(f"Saved color is: {digit_color}, saved state is: {digit_color_state}, saved colon color is: {colon_color}, saved colon state is: {colon_color_state}, saved brightness is: {brightness}")

def run():
    global time_valid, requested_render, brightness, clock_state

    read_history()
    startup()
    clock_state = ClockStates.BRIGHTNESS
    state_loops = 0
    display_timer = Timer(period=50, mode=Timer.PERIODIC, callback=update_display)
    last_dst = True
    dst_lockout = False

    # Main Loop!!
    while True:
        t = rtc.get_time()
        tutc = time.mktime(t)
        years = t[0]

        if not is_valid_time(years):
            requested_render = (-1, -1, -1, True, neo.c_red, neo.c_white, 0)
            time.sleep(1.0)
            sync.sync_time(tutc, True)
            continue

        colon_color_override = update_colon_color(tutc, hist.get_last_time_check())

        tlocal = apply_timezone_offset(t, last_dst)

        if not dst_lockout:
            new_dst = th.daylight_savings_check(tlocal)
            last_dst, tlocal, dst_lockout = handle_dst_change(new_dst, last_dst, t)

        h, m, s = tlocal[3], tlocal[4], tlocal[5]
        is_am = h < 12
        h12 = th.h24_to_h12(h)

        dc1, dc2, blink_period = critical_time_check(tlocal)

        requested_render = (h12, m, s, is_am, dc2, colon_color_override, blink_period)
        time.sleep(0.01)

        if clock_state == ClockStates.BRIGHTNESS:
            check_encoder_for_brightness(h12, m, s, is_am, display_timer)
        if clock_state == ClockStates.DIGIT_COLOR:
            check_encoder_for_color_changes(h12, m, s, is_am, display_timer)
        if clock_state == ClockStates.COLON_COLOR:
            check_encoder_for_color_changes(h12, m, s, is_am, display_timer)
        if clock_state == ClockStates.SECONDS_COLOR:
            check_encoder_for_color_changes(h12, m, s, is_am, display_timer)
        if clock_state == ClockStates.AM_COLOR:
            check_encoder_for_color_changes(h12, m, s, is_am, display_timer)

        if encoder.did_button_press():
            clock_state += 1
            draw_menu_light()
            if clock_state == ClockStates.RAINBOW:
                # def rainbow_animation(loops=50, dim_amount=.93, initial_brightness=0.1, speed=56):
                neo.rainbow_animation(600, 0.93, brightness)
                clock_state = ClockStates.BRIGHTNESS
            print("State: ", clock_state)
            state_loops = 300;

        # This returns you to the first state if you don't press a button after 300 loops
        if state_loops > 0:
            state_loops -= 1
            if state_loops <= 0:
                clock_state = ClockStates.BRIGHTNESS
                print("State: ", clock_state)

                
# Helper method for checking encoder and then updating brightness
def check_encoder_for_brightness(h12, m, s, is_am, timer):
    '''Reads the encoder for brightness changes and updates the brightness.

    Continuously monitors the encoder while it is changing, adjusting the brightness
    according to the encoder direction.
    '''
    global brightness, digit_color, colon_color
    encoderValue = encoder.read_encoder()

    if encoderValue != encoder.EncoderResult.NO_CHANGE:
        encoder_loops = 80
        stop_timer(timer) #stops timer so it won't interrupt

        while True:  # looping to keep focus on encoder and not miss steps
            if encoderValue != encoder.EncoderResult.NO_CHANGE:
                change_brightness(encoderValue)
                neo.render_time(h12, m, s, is_am, digit_color, colon_color, seconds_color, am_color, brightness)
                neo.show()
                encoder_loops = 80  # loops 80 times at .01 sleep. So stays in this loop about .8s after the last encoder change

            time.sleep(0.01)
            encoderValue = encoder.read_encoder()
            encoder_loops -= 1

            if encoder_loops < 0:
                print("encoder loop break")
                hist.write_brightness(brightness)
                start_timer(timer) #re-starts timer
                break

def check_encoder_for_color_changes(h12, m, s, is_am, timer):
    '''Reads the encoder for color changes and updates the color based on the clock state.

    Continuously monitors the encoder while it is changing, adjusting the color
    according to the current clock state. This function ensures the color updates
    smoothly, taking into account the direction and speed of the encoder rotation.
    '''
    encoderValue = encoder.read_encoder()

    color, color_state = get_current_color()

    if encoderValue != encoder.EncoderResult.NO_CHANGE:
        encoder_loops = 1
        stop_timer(timer) #stops timer so it won't interrupt

        while True:  # looping to keep focus on encoder and not miss steps
            if encoderValue != encoder.EncoderResult.NO_CHANGE:
                color, color_state = change_color(color, color_state, encoderValue, encoder_loops)
                set_current_color(color, color_state)
                draw_color_box(h12, m, s, is_am)
                encoder_loops = 80  # loops 80 times at .01 sleep. So stays in this loop about .8s after the last encoder change

            time.sleep(0.01)
            encoderValue = encoder.read_encoder()
            encoder_loops -= 1

            if encoder_loops < 0:
                print("encoder color loop break")
                start_timer(timer) #re-starts timer
                save_colors()
                break
            
def draw_color_box(h12, m, s, is_am):
    '''draws a box around the thing you are changing the color of'''
    if clock_state == ClockStates.DIGIT_COLOR: 
        neo.draw_vert_line(0, 0, 7, neo.dim_color(digit_color, brightness))
        neo.draw_vert_line(24, 0, 7, neo.dim_color(digit_color, brightness))
        neo.draw_horz_line(7, 0, 24, neo.dim_color(digit_color, brightness))
        neo.draw_horz_line(0, 0, 24, neo.dim_color(digit_color, brightness))
    elif clock_state == ClockStates.COLON_COLOR:
        neo.draw_vert_line(10, 1, 5, neo.dim_color(colon_color, brightness))
        neo.draw_vert_line(12, 1, 5, neo.dim_color(colon_color, brightness))
        neo.draw_horz_line(1, 10, 12, neo.dim_color(colon_color, brightness))
        neo.draw_horz_line(5, 10, 12, neo.dim_color(colon_color, brightness))
    elif clock_state == ClockStates.SECONDS_COLOR:
        neo.draw_vert_line(24, 7, 5, neo.dim_color(seconds_color, brightness))
        neo.draw_horz_line(5, 24, 31, neo.dim_color(seconds_color, brightness))
    elif clock_state == ClockStates.AM_COLOR:
        neo.draw_vert_line(24, 0, 3, neo.dim_color(am_color, brightness))
        neo.draw_vert_line(31, 0, 3, neo.dim_color(am_color, brightness))
        neo.draw_horz_line(3, 24, 31, neo.dim_color(am_color, brightness))
        neo.draw_horz_line(0, 24, 31, neo.dim_color(am_color, brightness))
    
    neo.render_time(h12, m, s, is_am, digit_color, colon_color, seconds_color, am_color, brightness)
    neo.show()

def draw_menu_light():
    '''draws a singe light showing what menu spot you're on so you know what the dial will do'''
    if clock_state == ClockStates.DIGIT_COLOR:
        neo.set_color(0, 7, neo.dim_color(digit_color, brightness))
    elif clock_state == ClockStates.COLON_COLOR:
        neo.set_color(1, 7, neo.dim_color(colon_color, brightness))
    elif clock_state == ClockStates.SECONDS_COLOR:
        neo.set_color(2, 7, neo.dim_color(seconds_color, brightness))
    elif clock_state == ClockStates.AM_COLOR:
        neo.set_color(3, 7, neo.dim_color(am_color, brightness))
    
def get_current_color():
    '''returns the color we are modifying based on what state we are in'''
    if clock_state == ClockStates.DIGIT_COLOR:
        return (digit_color, digit_color_state)
    elif clock_state == ClockStates.COLON_COLOR:
        return (colon_color, colon_color_state)
    elif clock_state == ClockStates.SECONDS_COLOR:
        return (seconds_color, seconds_color_state)
    elif clock_state == ClockStates.AM_COLOR:
        return (am_color, am_color_state)
    
def set_current_color(color, color_state):
    '''sets the new color and color state depending on what clock state we are in'''
    global digit_color, colon_color, digit_color_state, colon_color_state, seconds_color, seconds_color_state, am_color, am_color_state
    if clock_state == ClockStates.DIGIT_COLOR:
        digit_color = color
        digit_color_state = color_state
    elif clock_state == ClockStates.COLON_COLOR:
        colon_color = color
        colon_color_state = color_state
    elif clock_state == ClockStates.SECONDS_COLOR:
        seconds_color = color
        seconds_color_state = color_state
    elif clock_state == ClockStates.AM_COLOR:
        am_color = color
        am_color_state = color_state
        
def save_colors():
    hist.write_colors(digit_color, digit_color_state, colon_color, colon_color_state, seconds_color, seconds_color_state, am_color, am_color_state)

def change_color(color, color_state, direction, encoder_loops):
    r, g, b = color
    last_state = color_state

    speed = int(COLOR_SPEED * encoder_loops / 80)

    if direction == encoder.EncoderResult.UP:
        r, g, b, color_state = next_color.next_color(r, g, b, color_state, speed, next_color.ColorDirection.UP)
    elif direction == encoder.EncoderResult.DOWN:
        r, g, b, color_state = next_color.next_color(r, g, b, color_state, speed, next_color.ColorDirection.DOWN)

    color = (r, g, b)

    # Uncomment the lines below if you want to print the color, speed, and state information... caution noisy 
    # print(f"color = {color} -- speed: {speed}")
    
    # Uncomment these lines if you only want the color state changes... less noisy
    # if color_state != last_state:
    # 		print(f"color state change {last_state} -> {color_state}")

    return (color, color_state)

def change_brightness(direction):
    '''Adjusts the brightness based on the specified direction.

    The brightness change amount is dynamically determined depending on the current brightness level.
    Incrementing and decrementing amounts vary for different brightness ranges.
    '''
    global brightness

    change_amount = 0.2

    if brightness >= 0.3:
        change_amount = 0.2
    elif brightness < 0.05:
        change_amount = 0.002
    elif brightness < 0.1:
        change_amount = 0.01
    elif brightness < 0.3:
        change_amount = 0.03

    if direction == encoder.EncoderResult.UP:
        brightness += change_amount
    else:
        brightness -= change_amount

    brightness = max(0.004, min(1, brightness))
    
    # Uncomment to see the current brightness levels as they are changed
    # print("Brightness: ", brightness)

        
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
