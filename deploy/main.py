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
# If there is no wifi saved, the first time it boots it will create an access point
# and display the access point's name and password as well as the ip address to visit
# You can select your wifi from that webpage, enter it's password, and reboot. If the device
# has a saved wifi ssid and password but can't connect to wifi it will create the access
# point again while the clock is running so you can update the saved wifi credentials
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
# be accessed manually by interacting with the code using Thorny. Brightness, colors, and
#render styles are also saved and retreeved in the eeprom
#

import machine
from machine import RTC
from machine import Timer
import history as hist
import neo
import ntptime as ntp
import rtcmod as rtc
import timehelp as th
import time
import next_color
import encoder
import clock_server as server
import access_point
import log
import gc
import render_styles as RenderStyles

Version = "V0.9, 12/10/23"
ClockId = "dev_unit"

class ClockStates:
    BRIGHTNESS = 1
    DIGIT_COLOR = 2
    COLON_COLOR = 3
    SECONDS_COLOR = 4
    AM_COLOR = 5
    WIFI = 6
    RENDER_STYLE = 7
    RAINBOW = 8
    
    
critical_times = [ ]
# Epic Robots at the School:
#    ((20, 50), (21, 05), (0, 1, 2, 3), neo.c_red, neo.c_white), 			#, 10),  removed blink period functionality now it blinks at a once per second period for all critical times 
#    ((02, 55), (03, 01), (0, 1, 2, 3, 4, 5, 6), neo.c_red, neo.c_white)] 	#,8)]

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
brightness = 0.2
is_connected = False

is_blink = False
crash_counter = 0
last_crash = 0

def update_display(timer):
    global blink_even, blink_counter, digit_color, brightness, is_blink, crash_counter, last_crash
    
    try:
        gc.collect()
        tlocal = find_time()

        digit_color_override, digit_blink_color = critical_time_check(tlocal)
        if is_blink: digit_color_override = digit_blink_color
        
        #todo fix colon color override for stale time
        #colon_color_override = update_colon_color(tlocal, hist.get_last_time_check())
        colon_color_override = colon_color
        
        #print(f"timer fired. Digit color: {digit_color}")

        neo.solid(neo.c_black)
        neo.render_time(h12, m, s, is_am, digit_color_override, colon_color_override, seconds_color, am_color, brightness, render_style)
        draw_menu_light()
        neo.show()
        is_blink = not is_blink
        last_s = s
        gc.collect()
        #if is_blink: raise Exception("Test exception in display timer!") #used to test the crash logging
    except Exception as e:
        crash_counter += 1
        current_time = time.time()
        if current_time - last_crash <= 10:  # If crashes occur within 10 seconds
            if crash_counter >= 10:
                log.log_exception(e, fatal=True)
                stop_timer() #let it just stop working to prevent spamming the log forever
            else:
                log.log_exception(e, fatal=False) #less than ten crashes in 10 seconds so logging as non fatal and the dipslay timer will call again
        else:
            crash_counter = 1  # Reset counter if more than 10 seconds have passed since last crash
        last_crash = current_time
    
dst_lockout = False
last_dst = True
def find_time():
    global h12, m, s, is_am, dst_lockout, last_dst
    t = rtc.get_time()
    tutc = time.mktime(t)
    years = t[0]

    if not is_valid_time(years):
        h12 = -1
        m = -1
        s = -1
        is_am = True
        return tutc
    
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

    h, m, s = tlocal[3], tlocal[4], tlocal[5]
    is_am = h < 12
    h12 = th.h24_to_h12(h)
    return tlocal

def is_valid_time(years):
    return years >= 2010

def update_colon_color(tutc, tlast_update):
    
    ### throwing error TODO:
    #File main.py line 177, in update_colon_color
    #TypeError: unsupported types for __sub__: ‘tuple’ ‘int’
    #tutc: (2024, 1, 13, 22, 0, 49, 5, 13), tlast_update 1705211931
    
    print(f"tutc: {tutc}, tlast_update: {tlast_update}")
    global colon_color
    if tutc - tlast_update > 30 * 24 * 3600:
        return (0,0,255)
    return colon_color
        
def critical_time_check(t):
    " Returns params for critical times, if active."
    wd = th.day_of_week(t)
    tchk = t[3] + (t[4] / 60.0)
    for ct in critical_times:
        t1, t2, wds, c1, c2 = ct
        tc1 = t1[0] + t1[1] / 60.0
        tc2 = t2[0] + t2[1] / 60.0
        if wd in wds:
            if tchk >= tc1 and tchk <= tc2:
                return (c1, c2)
    return (digit_color, digit_color)

def wait_for_network_time(must_connect = False):
    global ssid, pw, ip
    '''Used at startup. Disables clock since no time to display.  Trys to
    connect to wifi.'''
    global time_valid
    icount = 0
    while True:
        neo.blue_square(0)
        print("Scanning for wifi: " + ssid)
        ntp.init()
        tstart = time.time()
        while True:
            access_point = ntp.find_ap(ssid)
            if access_point is not None: break
            print("Access point not found")
            icount += 1
            neo.blue_square(icount, (40, 0, 40))
            time.sleep(0.5)
            if time.time() - tstart > 30:
                neo.show_no_wifi()
                time.sleep(5.0)
                tstart = time.time()
                neo.blue_square(0)
                if not must_connect: return ("","")
        ssid, bssid, chan, signal, _, _= access_point
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
            if not must_connect: return ssid, pw
            neo.blue_square(0)
            continue
        ip = ntp.get_ip()
        print("ip address from ntp: " + ip)
        neo.show_wifi_ok(ip)
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
            if not must_connect: return ssid, pw
            continue
        rtc.set_time(time.localtime(t))
        hist.time_check(t)
        str_tme = str(time.localtime(t))
        print("NTP Time Recevied.")
        print("Setting RTC Module to UTC Time: %s" % str_tme)
        neo.show_ntp_ok()
        time.sleep(2.0)
        ntp.network_off()
        time_valid = True
        return ssid, pw
            
def startup():
    global time_valid
    print("Clock Startup. Id=%s   Version=%s" % (ClockId, Version))
    read_history()
    neo.set_global_brightness(brightness)
    
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
    ssid, pw = wait_for_network_time(must_connect = not time_valid)

def start_timer():
    display_timer.init(period=500, mode=Timer.PERIODIC, callback=update_display)
    
def stop_timer():
    display_timer.deinit()
    
def read_history():
    '''reads the history from eeprom and saves it to our global variables'''
    global brightness, digit_color, digit_color_state, colon_color, colon_color_state, seconds_color, seconds_state, am_color, am_color_state, render_style

    try:
        brightness = hist.read_brightness()

        if brightness <= 0:
            brightness = 0.04
        elif brightness > 1:
            brightness = 1

        digit_color, digit_color_state, colon_color, colon_color_state, seconds_color, seconds_color_state, am_color, am_color_state = hist.read_colors()
        
        render_style = hist.read_render_style()
    except Exception as e:
        print("could not read history! Excepion is: ",e)
    print(f"Saved color is: {digit_color}, saved state is: {digit_color_state}, saved colon color is: {colon_color}, saved colon state is: {colon_color_state}, saved brightness is: {brightness}, render style: {render_style}")

def has_been_setup():
    global ssid, pw
    ssid, pw = hist.read_wifi()
    print(f"SSID and PW from History: \"{ssid}\", \"{pw}\"")
    if ssid == "" or pw == "": return False
    else: return True

def run():
    global time_valid, brightness, clock_state, digit_color, colon_color, seconds_color, am_color, display_timer, is_connected
    if not has_been_setup():
        access_point.run(access_point.scroll_text)
        machine.soft_reset() #should never get here. access_point should loop forever
        
    startup()
    clock_state = ClockStates.BRIGHTNESS
    state_loops = 0
    display_timer = Timer(period=500, mode=Timer.PERIODIC, callback=update_display)
    
    #connect to the server
    is_connected = server.connect_wifi(ssid, pw)
    
    try:
        if not is_connected: access_point.run(on_loop)
        
        count = 0
        while not is_connected:
            on_loop()
            time.sleep(.01)
            if count >= 10000:
                count = 0
                is_connected = server.connect_wifi(ssid, pw)
        
        #start the sever loop to continually listen for for connections. Pass in on_loop function to be ran each loop
        server.start_server_loop(get_colors_for_server, update_colors_from_server, play_rainbow, draw_message_from_server, on_loop, toggle_render_style)
    except Exception as e:
        log.log_exception(e)
        print ("server crashed!!!!")
        print (f"Error: {e}")
    finally:
        #if we get here the main loop exited for some reason.
        print("Resetting!!!!")
        machine.soft_reset()

state_loops = 0
def on_loop():
    global clock_state, state_loops
    if clock_state == ClockStates.BRIGHTNESS:
        check_encoder_for_brightness()
    if clock_state == ClockStates.DIGIT_COLOR:
        check_encoder_for_color_changes()
    if clock_state == ClockStates.COLON_COLOR:
        check_encoder_for_color_changes()
    if clock_state == ClockStates.SECONDS_COLOR:
        check_encoder_for_color_changes()
    if clock_state == ClockStates.AM_COLOR:
        check_encoder_for_color_changes()
    if clock_state == ClockStates.WIFI:
        show_ip()
        clock_state = ClockStates.RENDER_STYLE
    if clock_state == ClockStates.RENDER_STYLE:
        check_encoder_for_render_style()
    if clock_state == ClockStates.RAINBOW:
        play_rainbow()
        clock_state = ClockStates.BRIGHTNESS
        state_loops = 0

    if encoder.did_button_press():
        clock_state += 1
        draw_menu_light()
        print("State: ", clock_state)
        state_loops = 300;

    # This returns you to the first state if you don't press a button after 300 loops
    if state_loops > 0:
        state_loops -= 1
        if state_loops <= 0:
            clock_state = ClockStates.BRIGHTNESS
            print("State: ", clock_state)
           
# Helper method for checking encoder and then updating brightness
def check_encoder_for_brightness():
    '''Reads the encoder for brightness changes and updates the brightness.

    Continuously monitors the encoder while it is changing, adjusting the brightness
    according to the encoder direction.
    '''
    global brightness, digit_color, colon_color
    encoderValue = encoder.read_encoder()

    if encoderValue != encoder.EncoderResult.NO_CHANGE:
        encoder_loops = 80
        stop_timer() #stops timer so it won't interrupt

        while True:  # looping to keep focus on encoder and not miss steps
            if encoderValue != encoder.EncoderResult.NO_CHANGE:
                change_brightness(encoderValue)
                neo.render_time(h12, m, s, is_am, digit_color, colon_color, seconds_color, am_color, brightness, render_style)
                neo.show()
                encoder_loops = 80  # loops 80 times at .01 sleep. So stays in this loop about .8s after the last encoder change

            time.sleep(0.01)
            encoderValue = encoder.read_encoder()
            encoder_loops -= 1

            if encoder_loops < 0:
                print("encoder loop break")
                save_brightness()
                start_timer() #re-starts timer
                break

def check_encoder_for_color_changes():
    '''Reads the encoder for color changes and updates the color based on the clock state.

    Continuously monitors the encoder while it is changing, adjusting the color
    according to the current clock state. This function ensures the color updates
    smoothly, taking into account the direction and speed of the encoder rotation.
    '''
    encoderValue = encoder.read_encoder()

    color, color_state = get_current_color()

    if encoderValue != encoder.EncoderResult.NO_CHANGE:
        encoder_loops = 1
        stop_timer() #stops timer so it won't interrupt

        while True:  # looping to keep focus on encoder and not miss steps
            if encoderValue != encoder.EncoderResult.NO_CHANGE:
                color, color_state = change_color(color, color_state, encoderValue, encoder_loops)
                set_current_color(color, color_state)                                
                neo.render_time(h12, m, s, is_am, digit_color, colon_color, seconds_color, am_color, brightness, render_style)
                neo.show()
                encoder_loops = 80  # loops 80 times at .01 sleep. So stays in this loop about .8s after the last encoder change

            time.sleep(0.01)
            encoderValue = encoder.read_encoder()
            encoder_loops -= 1

            if encoder_loops < 0:
                print("encoder color loop break")
                start_timer() #re-starts timer
                save_colors()
                break
            
def check_encoder_for_render_style():
    '''Reads the encoder for render style changes.

    Continuously monitors the encoder while it is changing, adjusting the brightness
    according to the encoder direction.
    '''
    global brightness, digit_color, colon_color
    encoderValue = encoder.read_encoder()

    if encoderValue != encoder.EncoderResult.NO_CHANGE:
        encoder_loops = 80
        stop_timer() #stops timer so it won't interrupt

        while True:  # looping to keep focus on encoder and not miss steps
            if encoderValue != encoder.EncoderResult.NO_CHANGE:
                toggle_render_style(encoderValue)
                neo.clear()
                neo.render_time(h12, m, s, is_am, digit_color, colon_color, seconds_color, am_color, brightness, render_style)
                neo.show()
                encoder_loops = 80  # loops 80 times at .01 sleep. So stays in this loop about .8s after the last encoder change

            time.sleep(0.01)
            encoderValue = encoder.read_encoder()
            encoder_loops -= 1

            if encoder_loops < 0:
                print("encoder loop break")
                save_render_style()
                start_timer() #re-starts timer
                break

def draw_menu_light():
    '''draws a singe light showing what menu spot you're on so you know what the dial will do'''
    if clock_state == ClockStates.DIGIT_COLOR:
        neo.set_color(0, 7, neo.dim_color(digit_color, brightness))
    elif clock_state == ClockStates.COLON_COLOR:
        neo.set_color(0, 6, neo.dim_color(colon_color, brightness))
    elif clock_state == ClockStates.SECONDS_COLOR:
        neo.set_color(0, 5, neo.dim_color(seconds_color, brightness))
    elif clock_state == ClockStates.AM_COLOR:
        neo.set_color(0, 4, neo.dim_color(am_color, brightness))
    elif clock_state == ClockStates.RENDER_STYLE:
        neo.set_color(0, 3, neo.dim_color(neo.c_blue, brightness))    
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
def save_brightness():
    hist.write_brightness(brightness)
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
    print(f"color = {color} -- speed: {speed} -- state: {color_state}")
    
    # Uncomment these lines if you only want the color state changes... less noisy
    if color_state != last_state:
        print(f"color state change {last_state} -> {color_state}")

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
    ap = ntp.find_ap(ssid)
    if ap is None:
        print("No access point found. Abort.")
        return
    ap_ssid, bssid, chan, signal, _, _ = ap
    print("Found AP.  Name=%s, Chan=%d, Signal=%d, PW=%s" % (ap_ssid, chan, signal, pw))
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


def update_colors_from_server(values):
    global digit_color, colon_color, seconds_color, am_color, brightness

    digit_color = tuple(map(int, values["digit_color"]))
    colon_color = tuple(map(int, values["colon_color"]))
    seconds_color = tuple(map(int, values["seconds_color"]))
    am_color = tuple(map(int, values["ampm_color"]))
    b =float(values["brightness"])
    brightness = b
    print(f"digit color = {digit_color}, brightness (local) = {b} brightness (global) {brightness}!!!!!!!!")
    
    print("Got a color update from the server: ", values)
    
    save_colors()
    save_brightness()
    
def get_colors_for_server():
    if is_am: am_or_pm = "am"
    else: am_or_pm = "pm"
    time_object = (f"{h12}",f"{m:02d}",f"{s:02d}",am_or_pm)
    return (digit_color, colon_color, seconds_color, am_color, brightness, get_time_string(), time_object)
    
def play_rainbow():
    stop_timer()
    neo.rainbow_animation(600, 0.93, brightness)
    start_timer()
    
def show_ip():
    stop_timer()
    if is_connected: neo.show_wifi_ok(ip)
    else: neo.scroll_text("  " + access_point.scroll_text, neo.dim_color(digit_color, brightness), .005)
    start_timer()
    
def get_time_string():
    if is_am: am_or_pm = "am"
    else: am_or_pm = "pm"
    return f"{h12}:{m:02d}:{s:02d} {am_or_pm}"

def draw_message_from_server(message, color, isLarge):
    stop_timer()
    neo.scroll_text(message,neo.dim_color(color, brightness), .05, isLarge)
    start_timer()
def save_render_style():
    hist.write_render_style(render_style)
    
def toggle_render_style(is_up = encoder.EncoderResult.UP):
    global render_style
    if is_up == encoder.EncoderResult.UP: render_style += 1;
    else: render_style -=1;
    if render_style >= len(RenderStyles.NAMES): render_style = 0
    if render_style < 0: render_style = len(RenderStyles.NAMES) - 1
    save_render_style()
    
    